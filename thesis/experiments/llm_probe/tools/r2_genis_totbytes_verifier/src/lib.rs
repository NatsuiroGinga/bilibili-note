#![deny(unsafe_op_in_unsafe_fn)]

mod archive;
mod cli;
mod flow;
mod model;
mod output;
mod packet;
mod pcapng;

pub use cli::Cli;

use anyhow::Result;

/// 执行一次完整、不可覆盖的 GeNIS `TotBytes` 口径审计。
pub fn run(cli: Cli) -> Result<()> {
    flow::run_verification(cli)
}
