use std::path::PathBuf;

use clap::Parser;

/// GeNIS `TotBytes` 全量逐包复算与网络层口径裁决。
#[derive(Debug, Parser)]
#[command(version, about)]
pub struct Cli {
    /// GeNIS 官方 `1-packets.zip` 本机路径。
    #[arg(long)]
    pub packet_archive: PathBuf,

    /// 本次源锁登记的 `1-packets.zip` SHA-256。
    #[arg(long)]
    pub packet_archive_sha256: String,

    /// GeNIS 官方 `2-flows.zip` 本机路径。
    #[arg(long)]
    pub flow_archive: PathBuf,

    /// 冻结的三源约一万条候选 JSONL 清单。
    #[arg(long)]
    pub candidate_manifest: PathBuf,

    /// 候选清单的冻结 SHA-256。
    #[arg(long)]
    pub candidate_manifest_sha256: String,

    /// 权威 PCAPNG 成员与 10 秒流 CSV 成员的一对一 JSONL 清单。
    #[arg(long)]
    pub member_map: PathBuf,

    /// 成员配对清单的冻结 SHA-256。
    #[arg(long)]
    pub member_map_sha256: String,

    /// 唯一正式输出目录；已存在时拒绝覆盖。
    #[arg(long)]
    pub output: PathBuf,

    /// 本次执行绑定的工具提交或不可变版本标识。
    #[arg(long)]
    pub tool_revision: String,

    /// 本次执行代码锁对象的 SHA-256。
    #[arg(long)]
    pub execution_code_lock_sha256: String,

    /// 预期 GeNIS 冻结候选数。
    #[arg(long, default_value_t = 3_973)]
    pub expected_candidate_count: usize,

    /// 预期原始包与 10 秒流成员配对数。
    #[arg(long, default_value_t = 11)]
    pub expected_member_count: usize,

    /// 流起止时间窗的固定边界容差；正式合同固定为 0。
    #[arg(long, default_value_t = 0)]
    pub time_tolerance_ns: u64,

    /// 单个 PCAPNG 块允许的最大字节数。
    #[arg(long, default_value_t = 16_777_216)]
    pub max_pcapng_block_bytes: usize,

    /// 内存中允许的最大冻结流绑定数。
    #[arg(long, default_value_t = 10_000)]
    pub max_flow_bindings: usize,

    /// 同时保留的最大 IP 分片上下文数。
    #[arg(long, default_value_t = 65_536)]
    pub max_fragment_contexts: usize,
}
