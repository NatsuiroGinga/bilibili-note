//! 两个合同测试共享的冻结模式夹具装载。
//!
//! 夹具 `fixtures/lspr24-v2-schema-audit.json` 由只读 Parquet 页脚导出（不读数据页），
//! 是本任务测试中 101 列名与类型的唯一来源，禁止在测试里手抄列清单。

#![allow(dead_code)]

use std::path::PathBuf;

use lspr24_g0::SchemaAudit;

/// 返回冻结模式夹具路径。
pub fn frozen_schema_audit_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join("lspr24-v2-schema-audit.json")
}

/// 读取冻结模式夹具的原始字节。
pub fn frozen_schema_audit_bytes() -> Vec<u8> {
    std::fs::read(frozen_schema_audit_path()).expect("冻结模式夹具应存在且可读")
}

/// 装载冻结的 101 列模式审计。
pub fn load_frozen_schema_audit() -> SchemaAudit {
    SchemaAudit::from_json(&frozen_schema_audit_bytes()).expect("冻结模式夹具应能通过审计解析")
}
