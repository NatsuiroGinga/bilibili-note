//! LSPR24 G0-A 收据结构与依赖归约入口。

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use lspr24_g0::{
    GateReceipt, OverallDecision, evaluate_receipts, parse_gate_config, parse_gate_receipt,
};

fn main() -> ExitCode {
    match run() {
        Ok(decision) => {
            println!("{{\"overall\":\"{}\"}}", decision_name(decision));
            decision_exit_code(decision)
        }
        Err(message) => {
            eprintln!("门禁输入无效：{message}");
            println!("{{\"overall\":\"NOT_READY\"}}");
            ExitCode::from(3)
        }
    }
}

fn run() -> Result<OverallDecision, String> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let config_path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| "必须提供唯一配置路径".to_owned())?;
    if arguments.next().is_some() {
        return Err("只允许一个配置路径参数".to_owned());
    }

    let config_bytes = fs::read(&config_path)
        .map_err(|error| format!("无法读取配置 {}：{error}", config_path.display()))?;
    let config = parse_gate_config(&config_bytes).map_err(|error| error.to_string())?;
    let base = config_path.parent().unwrap_or_else(|| Path::new("."));
    let mut receipts = Vec::with_capacity(config.receipt_paths().len());
    for path in config.receipt_paths().values() {
        let path = if path.is_absolute() {
            path.clone()
        } else {
            base.join(path)
        };
        let bytes = fs::read(&path)
            .map_err(|error| format!("无法读取收据 {}：{error}", path.display()))?;
        let receipt = parse_gate_receipt(&bytes).map_err(|error| error.to_string())?;
        receipts.push(receipt);
    }

    Ok(evaluate_without_raw_predicates(&config, &receipts).overall())
}

fn evaluate_without_raw_predicates(
    config: &lspr24_g0::GateConfig,
    receipts: &[GateReceipt],
) -> lspr24_g0::GateEvaluation {
    // 任务 5 接入逐项原始制品谓词前，禁止把生产者汇总字段冒充独立复算结果。
    evaluate_receipts(config, receipts, &BTreeMap::new())
}

const fn decision_name(decision: OverallDecision) -> &'static str {
    match decision {
        OverallDecision::NoGo => "NO_GO",
        OverallDecision::NotReady => "NOT_READY",
        OverallDecision::GoToBaselinesAndEarlyStopping => {
            "GO_TO_BASELINES_AND_EARLY_STOPPING"
        }
        OverallDecision::GoToBaselinesThirdOnly => "GO_TO_BASELINES_THIRD_ONLY",
    }
}

fn decision_exit_code(decision: OverallDecision) -> ExitCode {
    match decision {
        OverallDecision::GoToBaselinesAndEarlyStopping
        | OverallDecision::GoToBaselinesThirdOnly => ExitCode::SUCCESS,
        OverallDecision::NoGo => ExitCode::from(2),
        OverallDecision::NotReady => ExitCode::from(3),
    }
}
