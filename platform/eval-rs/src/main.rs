//! 第五章评测服务对比：Rust axum + tch-rs (libtorch, MPS) 侧。
//!
//! 与 `platform/eval-py/app.py` 共用：
//! - 同一 safetensors 权重（`model_manifest.json` 给出路径与 SHA-256，启动时校验）；
//! - 同一 HTTP 契约：`POST /eval` 裸 little-endian float32 `(n, 4561)`，`1 <= n <= 32`；
//! - 同一层序与算子顺序，保证数值可逐元素对照。
//!
//! 构建（libtorch 取自 Python 的 torch 安装；tch pin 到声明 PyTorch 2.12.0 的提交
//! d5bbf6fe6cdbb06006aac5cb673be3c8d029c24b，无需 bypass 版本检查）：
//! ```bash
//! platform/eval-rs/build.sh
//! ```
//! 运行需要 `DYLD_LIBRARY_PATH` 指向 Python torch 的 `lib/`，见 `run.sh`。

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Instant;

use axum::body::Bytes;
use axum::extract::State;
use axum::http::StatusCode;
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tch::{Device, Kind, Tensor};

const MAX_BATCH: usize = 32;

#[derive(Deserialize)]
struct Manifest {
    k: i64,
    input_dim: i64,
    weights_path: String,
    weights_sha256: String,
}

struct Layer {
    weight: Tensor,
    bias: Tensor,
    r: Tensor,
    s: Tensor,
    beta: Tensor,
}

struct Model {
    k: i64,
    input_dim: i64,
    layers: Vec<Layer>,
}

impl Model {
    /// 与 `ch4_lamda_tabm_pilot.TabMMLP.forward` 逐算子对应：
    /// 首层先按 r 展开成员轴；每层 `y = s ⊙ (W(r ⊙ x) + b) + β`；
    /// enc1–cls2 后接 ReLU（Dropout 在 eval 下为恒等）；cls3 后 sigmoid，再对成员取均值。
    fn forward(&self, x: &Tensor) -> Tensor {
        let b = x.size()[0];
        let mut h = x
            .unsqueeze(1)
            .expand([b, self.k, self.input_dim], false)
            .multiply(&self.layers[0].r);
        let last = self.layers.len() - 1;
        for (i, layer) in self.layers.iter().enumerate() {
            h = h.matmul(&layer.weight.transpose(0, 1)) + &layer.bias;
            h = layer.s.multiply(&h) + &layer.beta;
            if i < last {
                h = h.relu();
            }
        }
        h.sigmoid().mean_dim(1, false, Kind::Float).reshape([-1])
    }
}

struct AppState {
    model: Mutex<Model>,
    input_dim: usize,
    k: i64,
    device: String,
    model_load_s: f64,
}

type ApiError = (StatusCode, Json<serde_json::Value>);

fn api_error(status: StatusCode, msg: impl Into<String>) -> ApiError {
    (status, Json(serde_json::json!({ "error": msg.into() })))
}

#[derive(Serialize)]
struct Health {
    status: &'static str,
    device: String,
    input_dim: i64,
    k: i64,
    model_load_s: f64,
}

#[derive(Serialize)]
struct EvalResponse {
    probs: Vec<f32>,
    batch: usize,
}

async fn health(State(state): State<Arc<AppState>>) -> Json<Health> {
    Json(Health {
        status: "ok",
        device: state.device.clone(),
        input_dim: state.input_dim as i64,
        k: state.k,
        model_load_s: state.model_load_s,
    })
}

async fn eval(
    State(state): State<Arc<AppState>>,
    body: Bytes,
) -> Result<Json<EvalResponse>, ApiError> {
    let input_dim = state.input_dim;
    let n_floats = body.len() / 4;
    if body.len() % 4 != 0 || n_floats % input_dim != 0 {
        return Err(api_error(
            StatusCode::BAD_REQUEST,
            "body is not a whole (n, input_dim) float32 matrix",
        ));
    }
    let n = n_floats / input_dim;
    if n == 0 || n > MAX_BATCH {
        return Err(api_error(
            StatusCode::BAD_REQUEST,
            format!("batch must be 1..{MAX_BATCH}, got {n}"),
        ));
    }

    let floats: Vec<f32> = body
        .chunks_exact(4)
        .map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    let x = Tensor::from_slice(&floats).reshape([n as i64, input_dim as i64]);

    let probs = tokio::task::spawn_blocking(move || {
        let model = state
            .model
            .lock()
            .map_err(|_| "model lock poisoned".to_string())?;
        let device = match state.device.as_str() {
            "mps" => Device::Mps,
            _ => Device::Cpu,
        };
        let y = model.forward(&x.to_device(device));
        let cpu = y.to_device(Device::Cpu).contiguous();
        Vec::<f32>::try_from(&cpu).map_err(|e| e.to_string())
    })
    .await
    .map_err(|e| api_error(StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?
    .map_err(|e| api_error(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    Ok(Json(EvalResponse { probs, batch: n }))
}

fn sha256_file(path: &std::path::Path) -> Result<String, String> {
    let data = std::fs::read(path).map_err(|e| format!("read {}: {e}", path.display()))?;
    let mut h = Sha256::new();
    h.update(data);
    Ok(hex::encode(h.finalize()))
}

fn load_tensor(
    map: &mut HashMap<String, Tensor>,
    name: &str,
    device: Device,
) -> Result<Tensor, String> {
    let t = map
        .remove(name)
        .ok_or_else(|| format!("missing weight {name}"))?
        .to_kind(Kind::Float)
        .to_device(device)
        .contiguous();
    Ok(t)
}

fn load_layer(map: &mut HashMap<String, Tensor>, prefix: &str, device: Device) -> Result<Layer, String> {
    Ok(Layer {
        weight: load_tensor(map, &format!("{prefix}.weight"), device)?,
        bias: load_tensor(map, &format!("{prefix}.bias"), device)?,
        r: load_tensor(map, &format!("{prefix}.r"), device)?,
        s: load_tensor(map, &format!("{prefix}.s"), device)?,
        beta: load_tensor(map, &format!("{prefix}.beta"), device)?,
    })
}

struct Args {
    manifest: std::path::PathBuf,
    host: String,
    port: u16,
    device: String,
}

fn parse_args() -> Result<Args, String> {
    let mut manifest = None;
    let mut host = "127.0.0.1".to_string();
    let mut port = 18082u16;
    let mut device = "mps".to_string();
    let mut it = std::env::args().skip(1);
    while let Some(a) = it.next() {
        match a.as_str() {
            "--manifest" => manifest = Some(it.next().ok_or("--manifest needs a value")?.into()),
            "--host" => host = it.next().ok_or("--host needs a value")?,
            "--port" => port = it.next().ok_or("--port needs a value")?.parse().map_err(|e| format!("bad --port: {e}"))?,
            "--device" => device = it.next().ok_or("--device needs a value")?,
            other => return Err(format!("unknown argument {other}")),
        }
    }
    Ok(Args {
        manifest: manifest.ok_or("--manifest is required")?,
        host,
        port,
        device,
    })
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tch::set_num_threads(1);
    tch::set_num_interop_threads(1);
    let args = parse_args()?;
    let t0 = Instant::now();
    let manifest: Manifest = serde_json::from_str(&std::fs::read_to_string(&args.manifest)?)?;
    let run_dir = args
        .manifest
        .parent()
        .and_then(|p| p.parent())
        .ok_or("manifest must live in <run>/model/")?;
    let weights = run_dir.join(&manifest.weights_path);
    let sha = sha256_file(&weights)?;
    if sha != manifest.weights_sha256 {
        return Err(format!(
            "weights sha256 mismatch: file={sha} manifest={}",
            manifest.weights_sha256
        )
        .into());
    }
    let device = match args.device.as_str() {
        "mps" => {
            if !tch::utils::has_mps() {
                return Err("MPS requested but libtorch reports no MPS".into());
            }
            Device::Mps
        }
        "cpu" => Device::Cpu,
        other => return Err(format!("unknown device {other}").into()),
    };

    let mut tensors: HashMap<String, Tensor> = Tensor::read_safetensors(&weights)?
        .into_iter()
        .collect();
    let mut layers = Vec::with_capacity(7);
    for prefix in ["enc1", "enc2", "enc3", "enc4", "cls1", "cls2", "cls3"] {
        layers.push(load_layer(&mut tensors, prefix, device)?);
    }
    let model = Model {
        k: manifest.k,
        input_dim: manifest.input_dim,
        layers,
    };
    // 强制一次前向，确保 MPS 权重与内核在健康检查前已就绪。
    let warm = Tensor::zeros([1, manifest.input_dim], (Kind::Float, device));
    let _ = model.forward(&warm);
    let model_load_s = t0.elapsed().as_secs_f64();
    println!(
        "[eval-rs] device={:?} input_dim={} k={} weights_sha256={}… model_load={:.3}s",
        device,
        manifest.input_dim,
        manifest.k,
        &sha[..16],
        model_load_s
    );

    let state = Arc::new(AppState {
        model: Mutex::new(model),
        input_dim: manifest.input_dim as usize,
        k: manifest.k,
        device: args.device.clone(),
        model_load_s,
    });
    let app = Router::new()
        .route("/health", get(health))
        .route("/eval", post(eval))
        .with_state(state);
    let addr = format!("{}:{}", args.host, args.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    println!("[eval-rs] listening on {addr}");
    axum::serve(listener, app).await?;
    Ok(())
}
