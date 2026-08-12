//! LSPR24 开发宽表单次物化入口。

use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use lspr24_g0::screen::{DevelopmentWideConfig, materialize_development_wide};

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("LSPR24 开发宽表物化失败：{error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os().skip(1);
    let config_path = PathBuf::from(arguments.next().ok_or("缺少开发宽表配置路径")?);
    if arguments.next().is_some() {
        return Err("只接受一个开发宽表配置路径".into());
    }
    let config = DevelopmentWideConfig::from_json(&fs::read(config_path)?)?;
    let receipt = materialize_development_wide(&config)?;
    println!("{}", serde_json::to_string(&receipt)?);
    Ok(())
}
