use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;

use anyhow::{Context, Result, ensure};
use arrow_array::{
    ArrayRef, BooleanArray, Int64Array, RecordBatch, StringArray, UInt64Array,
};
use arrow_schema::{DataType, Field, Schema};
use parquet::arrow::ArrowWriter;
use parquet::basic::Compression;
use parquet::file::properties::WriterProperties;
use serde::Serialize;

use crate::archive::hash_file;
use crate::model::{ArtifactEntry, ComparisonRow};

pub struct OutputTransaction {
    final_path: PathBuf,
    partial_path: PathBuf,
    published: bool,
}

impl OutputTransaction {
    pub fn new(final_path: &Path) -> Result<Self> {
        ensure!(!final_path.exists(), "正式输出目录已存在，拒绝覆盖");
        let file_name = final_path
            .file_name()
            .and_then(|value| value.to_str())
            .context("正式输出目录缺少合法 UTF-8 basename")?;
        let partial_path = final_path.with_file_name(format!("{file_name}.partial"));
        ensure!(!partial_path.exists(), "临时输出目录已存在，拒绝覆盖");
        let parent = final_path.parent().context("正式输出目录缺少父目录")?;
        fs::create_dir_all(parent).with_context(|| format!("无法创建输出父目录：{}", parent.display()))?;
        fs::create_dir(&partial_path)
            .with_context(|| format!("无法创建临时输出目录：{}", partial_path.display()))?;
        Ok(Self {
            final_path: final_path.to_path_buf(),
            partial_path,
            published: false,
        })
    }

    pub fn path(&self, relative_path: &str) -> PathBuf {
        self.partial_path.join(relative_path)
    }

    pub fn publish(mut self) -> Result<()> {
        File::open(&self.partial_path)
            .context("无法打开临时输出目录进行同步")?
            .sync_all()
            .context("同步临时输出目录失败")?;
        fs::rename(&self.partial_path, &self.final_path)
            .context("同文件系统原子发布正式输出目录失败")?;
        self.published = true;
        if let Some(parent) = self.final_path.parent() {
            File::open(parent)
                .context("无法打开正式输出父目录进行同步")?
                .sync_all()
                .context("同步正式输出父目录失败")?;
        }
        Ok(())
    }
}

impl Drop for OutputTransaction {
    fn drop(&mut self) {
        if !self.published && self.partial_path.exists() {
            let _ = fs::remove_dir_all(&self.partial_path);
        }
    }
}

pub fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .with_context(|| format!("无法创建 JSON 制品：{}", path.display()))?;
    let mut writer = BufWriter::with_capacity(1024 * 1024, file);
    serde_json::to_writer_pretty(&mut writer, value).context("序列化 JSON 制品失败")?;
    writer.write_all(b"\n").context("写入 JSON 换行失败")?;
    writer.flush().context("刷新 JSON 制品失败")?;
    writer.get_ref().sync_all().context("同步 JSON 制品失败")?;
    Ok(())
}

pub fn write_comparison_parquet(path: &Path, rows: &[ComparisonRow]) -> Result<()> {
    let schema = Arc::new(Schema::new(vec![
        Field::new("scope", DataType::Utf8, false),
        Field::new("sample_id", DataType::Utf8, true),
        Field::new("group_id", DataType::Utf8, false),
        Field::new("flow_count", DataType::UInt64, false),
        Field::new("csv_packet_count", DataType::UInt64, false),
        Field::new("recomputed_packet_count", DataType::UInt64, false),
        Field::new("csv_tot_bytes", DataType::UInt64, false),
        Field::new("l2_wire_bytes", DataType::UInt64, false),
        Field::new("l3_network_bytes", DataType::UInt64, false),
        Field::new("l2_minus_csv", DataType::Int64, false),
        Field::new("l3_minus_csv", DataType::Int64, false),
        Field::new("l2_exact_match", DataType::Boolean, false),
        Field::new("l3_exact_match", DataType::Boolean, false),
        Field::new("match_status", DataType::Utf8, false),
        Field::new("identity_status", DataType::Utf8, false),
        Field::new("dur_inverse_count", DataType::UInt64, false),
        Field::new("dur_interval_lower_ns", DataType::Int64, true),
        Field::new("dur_interval_upper_ns", DataType::Int64, true),
        Field::new("actual_duration_ns", DataType::Int64, true),
        Field::new("dur_interval_match", DataType::Boolean, false),
        Field::new("source_binding_sha256", DataType::Utf8, false),
        Field::new("evidence_sha256", DataType::Utf8, false),
    ]));
    let columns: Vec<ArrayRef> = vec![
        Arc::new(StringArray::from_iter_values(rows.iter().map(|row| row.scope))),
        Arc::new(StringArray::from_iter(rows.iter().map(|row| row.sample_id.as_deref()))),
        Arc::new(StringArray::from_iter_values(rows.iter().map(|row| row.group_id.as_str()))),
        Arc::new(UInt64Array::from_iter_values(rows.iter().map(|row| row.flow_count))),
        Arc::new(UInt64Array::from_iter_values(rows.iter().map(|row| row.csv_packet_count))),
        Arc::new(UInt64Array::from_iter_values(rows.iter().map(|row| row.recomputed_packet_count))),
        Arc::new(UInt64Array::from_iter_values(rows.iter().map(|row| row.csv_tot_bytes))),
        Arc::new(UInt64Array::from_iter_values(rows.iter().map(|row| row.l2_wire_bytes))),
        Arc::new(UInt64Array::from_iter_values(rows.iter().map(|row| row.l3_network_bytes))),
        Arc::new(Int64Array::from_iter_values(rows.iter().map(|row| row.l2_minus_csv))),
        Arc::new(Int64Array::from_iter_values(rows.iter().map(|row| row.l3_minus_csv))),
        Arc::new(BooleanArray::from_iter(
            rows.iter().map(|row| Some(row.l2_exact_match)),
        )),
        Arc::new(BooleanArray::from_iter(
            rows.iter().map(|row| Some(row.l3_exact_match)),
        )),
        Arc::new(StringArray::from_iter_values(rows.iter().map(|row| row.match_status))),
        Arc::new(StringArray::from_iter_values(
            rows.iter().map(|row| row.identity_status),
        )),
        Arc::new(UInt64Array::from_iter_values(
            rows.iter().map(|row| row.dur_inverse_count),
        )),
        Arc::new(Int64Array::from_iter(
            rows.iter().map(|row| row.dur_interval_lower_ns),
        )),
        Arc::new(Int64Array::from_iter(
            rows.iter().map(|row| row.dur_interval_upper_ns),
        )),
        Arc::new(Int64Array::from_iter(
            rows.iter().map(|row| row.actual_duration_ns),
        )),
        Arc::new(BooleanArray::from_iter(
            rows.iter().map(|row| Some(row.dur_interval_match)),
        )),
        Arc::new(StringArray::from_iter_values(
            rows.iter().map(|row| row.source_binding_sha256.as_str()),
        )),
        Arc::new(StringArray::from_iter_values(
            rows.iter().map(|row| row.evidence_sha256.as_str()),
        )),
    ];
    let batch = RecordBatch::try_new(schema.clone(), columns).context("构造 Parquet 记录批失败")?;
    let properties = WriterProperties::builder()
        .set_compression(Compression::UNCOMPRESSED)
        .set_created_by("r2_genis_totbytes_verifier/0.1.0".to_owned())
        .set_max_row_group_size(8_192)
        .build();
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .with_context(|| format!("无法创建 Parquet 制品：{}", path.display()))?;
    let mut writer = ArrowWriter::try_new(file, schema, Some(properties))
        .context("创建 Parquet 写入器失败")?;
    writer.write(&batch).context("写入 Parquet 记录批失败")?;
    let metadata = writer.close().context("关闭 Parquet 写入器失败")?;
    ensure!(metadata.num_rows == i64::try_from(rows.len()).context("Parquet 行数转换失败")?, "Parquet 元数据行数与输入不一致");
    File::open(path).context("重新打开 Parquet 制品失败")?.sync_all().context("同步 Parquet 制品失败")?;
    Ok(())
}

pub fn artifact_entry(root: &Path, relative_path: &str) -> Result<ArtifactEntry> {
    let digest = hash_file(&root.join(relative_path))?;
    Ok(ArtifactEntry {
        relative_path: relative_path.to_owned(),
        size_bytes: digest.size_bytes,
        sha256: digest.sha256,
    })
}

pub fn command_version(program: &str, arguments: &[&str]) -> Result<String> {
    let output = Command::new(program)
        .args(arguments)
        .output()
        .with_context(|| format!("无法执行 {program} 记录工具链版本"))?;
    ensure!(output.status.success(), "{program} 工具链版本命令失败");
    let stdout = String::from_utf8(output.stdout).context("工具链版本输出不是 UTF-8")?;
    let value = stdout.trim().to_owned();
    ensure!(!value.is_empty(), "{program} 工具链版本输出为空");
    Ok(value)
}

pub fn peak_rss_bytes() -> Result<u64> {
    let mut usage = std::mem::MaybeUninit::<libc::rusage>::uninit();
    // SAFETY: `getrusage` 在成功时完整初始化调用方提供的 `rusage`，指针有效且仅在本调用中使用。
    let status = unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) };
    ensure!(status == 0, "getrusage 无法取得峰值常驻内存");
    // SAFETY: 上一条系统调用已返回成功，因此结构体已经完整初始化。
    let usage = unsafe { usage.assume_init() };
    let raw = u64::try_from(usage.ru_maxrss).context("峰值常驻内存为负数")?;
    #[cfg(target_os = "linux")]
    {
        raw.checked_mul(1024).context("Linux 峰值常驻内存换算溢出")
    }
    #[cfg(target_os = "macos")]
    {
        Ok(raw)
    }
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    {
        anyhow::bail!("当前平台未定义 ru_maxrss 的字节换算")
    }
}
