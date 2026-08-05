use clap::Parser;
use r2_genis_totbytes_verifier::{Cli, run};

fn main() {
    let cli = Cli::parse();
    if let Err(error) = run(cli) {
        eprintln!("错误：{error:#}");
        std::process::exit(1);
    }
}
