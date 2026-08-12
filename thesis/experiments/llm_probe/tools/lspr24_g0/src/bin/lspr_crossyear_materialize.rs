//! LSPR23 到 LSPR24 跨年度开发数据物化入口。

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use lspr24_g0::{CrossyearConfig, materialize_crossyear};

const HELP: &str = "用法：lspr_crossyear_materialize --config <配置文件>\n\n仅支持 bounded_quick_cache 模式，不生成全量主产品或全量侧车。\n\n参数：\n  --config <路径>  严格 JSON 配置路径\n  -h, --help       显示帮助\n";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("跨年度物化失败：{error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut arguments = env::args_os().skip(1);
    let Some(first) = arguments.next() else {
        print!("{HELP}");
        return Ok(());
    };
    if first == "-h" || first == "--help" {
        if arguments.next().is_some() {
            return Err("帮助参数后不能附加其他参数".into());
        }
        print!("{HELP}");
        return Ok(());
    }
    if first != "--config" {
        return Err("只接受 --config <配置文件> 或 --help".into());
    }
    let config_path = PathBuf::from(arguments.next().ok_or("--config 缺少路径")?);
    if arguments.next().is_some() {
        return Err("配置路径后不能附加其他参数".into());
    }
    let config = CrossyearConfig::from_json(&fs::read(&config_path)?)?;
    let receipt = materialize_crossyear(&config)?;
    println!("{}", serde_json::to_string(&receipt)?);
    Ok(())
}
