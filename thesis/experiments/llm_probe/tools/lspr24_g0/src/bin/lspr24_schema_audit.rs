//! LSPR24 冻结模式审计与双清单冻结入口。
//!
//! 只读取 Parquet 页脚元数据（列名、类型、行数、行组数），不构造数据页读取器，
//! 不读取任何数据行，也不输出任何行内容。

use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use lspr24_g0::{SchemaAudit, build_field_manifest, write_field_manifest_json};

const SCHEMA_AUDIT_FILE_NAME: &str = "schema-audit.json";
const DEDUP_PROJECTION_FILE_NAME: &str = "dedup-projection-manifest.json";
const FIELD_MANIFEST_FILE_NAME: &str = "field-manifest.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("模式审计失败：{message}");
            ExitCode::from(2)
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let parquet_path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| "用法：lspr24_schema_audit <parquet 路径> <输出目录>".to_owned())?;
    let output_directory = arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| "用法：lspr24_schema_audit <parquet 路径> <输出目录>".to_owned())?;
    if arguments.next().is_some() {
        return Err("只允许 Parquet 路径与输出目录两个参数".to_owned());
    }

    std::fs::create_dir_all(&output_directory).map_err(|error| {
        format!(
            "无法创建输出目录 {}：{error}",
            output_directory.display()
        )
    })?;

    let audit = SchemaAudit::from_parquet_footer(&parquet_path).map_err(|error| error.to_string())?;
    let projection = audit.dedup_projection_manifest();
    let entries = build_field_manifest(&audit).map_err(|error| error.to_string())?;

    let audit_digest = audit
        .write_json(output_directory.join(SCHEMA_AUDIT_FILE_NAME))
        .map_err(|error| error.to_string())?;
    let projection_digest = projection
        .write_json(output_directory.join(DEDUP_PROJECTION_FILE_NAME))
        .map_err(|error| error.to_string())?;
    let manifest_digest =
        write_field_manifest_json(&entries, output_directory.join(FIELD_MANIFEST_FILE_NAME))
            .map_err(|error| error.to_string())?;

    println!("{{");
    println!("  \"column_count\": {},", audit.columns().len());
    println!("  \"row_count\": {},", audit.row_count());
    println!("  \"row_group_count\": {},", audit.row_group_count());
    println!(
        "  \"schema_sha256\": \"{}\",",
        encode_hex(&audit.schema_sha256())
    );
    println!(
        "  \"dedup_content_column_count\": {},",
        projection.content_columns().len()
    );
    println!(
        "  \"dedup_excluded_column_count\": {},",
        projection.excluded_columns().len()
    );
    println!("  \"field_manifest_entry_count\": {},", entries.len());
    println!(
        "  \"{SCHEMA_AUDIT_FILE_NAME}\": \"{}\",",
        encode_hex(&audit_digest)
    );
    println!(
        "  \"{DEDUP_PROJECTION_FILE_NAME}\": \"{}\",",
        encode_hex(&projection_digest)
    );
    println!(
        "  \"{FIELD_MANIFEST_FILE_NAME}\": \"{}\"",
        encode_hex(&manifest_digest)
    );
    println!("}}");
    Ok(())
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}
