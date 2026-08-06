//! 合同 v5 绑定回归测试。
//!
//! 本测试是合同哈希重绑定的唯一机器化回归网：代码常量、冻结合同正文的实际
//! SHA-256、开发配置声明三者必须完全一致，并且合同正文必须真实包含 v5 的两处
//! 修订条文（`utc_ns` 冻结实现与 `External_*` string 映射）。任何一处漂移都会
//! 让 G0-D 运行收据绑定到错误的合同文本，因此这里逐项断言。
//!
//! 冻结合同正文位于 `.Codex/` 共享工作记忆，未纳入 Git 跟踪，因此只能在运行时
//! 读取，不能用 `include_str!` 编译期嵌入（否则缺少工作记忆的检出会直接编译失败）。
//! 合同缺失时本测试如实失败并给出精确路径，不做静默跳过。

use std::fs;
use std::path::PathBuf;

use lspr24_g0::{LSPR24_G0_CONTRACT_SHA256, LSPR24_G0_CONTRACT_VERSION, sha256};

/// 开发运行配置正文（文件名保持 v4，内部 contract 字段绑定当前合同）。
const DEVELOPMENT_CONFIG_TEXT: &str = include_str!("../configs/lspr24-g0-development-v4.json");

/// 本轮修订后的合同版本串。
const EXPECTED_CONTRACT_VERSION: &str = "lspr24-g0-v5-staged";

/// 冻结合同正文相对仓库根的路径。
const CONTRACT_RELATIVE_PATH: &str = ".Codex/docs/RWKV/2026-08-05-LSPR24-G0数据与切分合同.md";

/// 定位冻结合同正文：从本 crate 根上溯五级到仓库根。
fn contract_path() -> PathBuf {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    for _ in 0..5 {
        assert!(path.pop(), "无法从 crate 根上溯到仓库根");
    }
    path.join(CONTRACT_RELATIVE_PATH)
}

/// 读取冻结合同正文字节；缺失即失败并报出精确路径。
fn contract_bytes() -> Vec<u8> {
    let path = contract_path();
    fs::read(&path).unwrap_or_else(|error| {
        panic!("无法读取冻结合同正文 {}：{error}", path.display());
    })
}

/// 读取冻结合同正文并按 UTF-8 解码。
fn contract_text() -> String {
    String::from_utf8(contract_bytes()).expect("冻结合同正文必须是合法 UTF-8")
}

/// 把 32 字节摘要转为小写十六进制串。
fn hex_lower(digest: &[u8; 32]) -> String {
    use std::fmt::Write as _;

    let mut text = String::with_capacity(64);
    for byte in digest {
        write!(&mut text, "{byte:02x}").expect("向 String 写入不会失败");
    }
    text
}

#[test]
fn contract_version_constant_is_v5() {
    assert_eq!(
        LSPR24_G0_CONTRACT_VERSION, EXPECTED_CONTRACT_VERSION,
        "代码常量必须绑定 v5 合同版本串"
    );
}

#[test]
fn contract_sha256_constant_matches_frozen_document() {
    let actual = hex_lower(&sha256(&contract_bytes()));
    assert_eq!(
        LSPR24_G0_CONTRACT_SHA256, actual,
        "代码常量必须等于冻结合同正文的实际 SHA-256"
    );
}

#[test]
fn frozen_document_declares_v5_header() {
    let text = contract_text();
    assert!(
        text.contains("- **合同版本**：`lspr24-g0-v5-staged`"),
        "合同版本头必须声明为 v5"
    );
}

#[test]
fn frozen_document_freezes_micros_to_nanos() {
    let text = contract_text();
    assert!(
        text.contains("utc_ns(x) = x × 1000"),
        "§2.2 必须写明 utc_ns 的唯一冻结实现为微秒乘 1000"
    );
    assert!(
        text.contains("受检查算术"),
        "§2.2 必须要求受检查算术并在溢出时隔离"
    );
}

#[test]
fn frozen_document_freezes_external_string_mapping() {
    let text = contract_text();
    assert!(
        text.contains("`External_*` 源类型必须为 Parquet string"),
        "§3.1 必须声明 External_* 源类型为 string"
    );
    assert!(
        text.contains("`\"0\"`→内部（被防御侧）、`\"1\"`→外部"),
        "§3.1 必须冻结 \"0\"→内部、\"1\"→外部 的映射"
    );
    assert!(
        !text.contains("`External_*` 必须是 Parquet 布尔类型"),
        "§3.1 的旧布尔类型条文必须被替换"
    );
}

#[test]
fn development_config_binds_same_contract() {
    let config: serde_json::Value =
        serde_json::from_str(DEVELOPMENT_CONFIG_TEXT).expect("开发配置必须是合法 JSON");
    assert_eq!(
        config["contract_version"].as_str(),
        Some(LSPR24_G0_CONTRACT_VERSION),
        "开发配置的 contract_version 必须与代码常量一致"
    );
    assert_eq!(
        config["contract_sha256"].as_str(),
        Some(LSPR24_G0_CONTRACT_SHA256),
        "开发配置的 contract_sha256 必须与代码常量一致"
    );
}
