//! LSPR24 G0-D 真实 Parquet 两阶段开发物化命令。

use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use lspr24_g0::{
    FormalDevelopmentConfig, prepare_unlabeled_development_split,
    run_formal_development_materialization,
};
use serde::Serialize;

#[derive(Serialize)]
struct CommandStatus {
    g0_d: &'static str,
    g0_f: &'static str,
    a12: &'static str,
    final_access_authorized: bool,
    development_row_count: u64,
    development_semantic_sha256: String,
    split_receipt_sha256: String,
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("LSPR24 G0-D 开发物化失败：{error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os().skip(1);
    let config_path = PathBuf::from(arguments.next().ok_or("缺少正式开发配置路径")?);
    if arguments.next().is_some() {
        return Err("只接受一个正式开发配置路径".into());
    }
    let config = FormalDevelopmentConfig::from_json(&fs::read(config_path)?)?;
    prepare_unlabeled_development_split(&config)?;
    let receipt = run_formal_development_materialization(&config)?;

    let status = CommandStatus {
        // 当前入口只产生切分和开发物化原始收据，其他核心收据缺失时必须失败关闭。
        g0_d: "NOT_READY",
        g0_f: "NOT_READY",
        a12: "NOT_READY",
        final_access_authorized: false,
        development_row_count: receipt.development_row_count(),
        development_semantic_sha256: encode_hex(&receipt.development_semantic_sha256()),
        split_receipt_sha256: encode_hex(&receipt.split_receipt_sha256()),
    };
    println!("{}", serde_json::to_string(&status)?);
    Ok(())
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}
