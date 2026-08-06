//! 有界排序段与确定性多路归并。

use std::cmp::Ordering;
use std::collections::BinaryHeap;
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::num::NonZeroUsize;
use std::path::{Path, PathBuf};

use crate::canonical::{DatasetSemanticHasher, sha256};
use crate::types::{
    EndpointRoleOrder, IntegerOverflow, Sha256Digest, SortableRecord, SourceRowIndex,
    StableSortKey,
};

const RUN_MAGIC: &[u8; 8] = b"LSPG0R01";

/// 外部排序的资源与临时目录配置。
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExternalSortConfig {
    work_dir: PathBuf,
    max_records_per_run: NonZeroUsize,
}

impl ExternalSortConfig {
    /// 创建配置；工作目录必须尚不存在。
    #[must_use]
    pub fn new(work_dir: impl AsRef<Path>, max_records_per_run: NonZeroUsize) -> Self {
        Self {
            work_dir: work_dir.as_ref().to_path_buf(),
            max_records_per_run,
        }
    }
}

/// 外部排序的确定性摘要。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExternalSortSummary {
    row_count: u64,
    dataset_sha256: Sha256Digest,
}

impl ExternalSortSummary {
    /// 返回输出记录数。
    #[must_use]
    pub const fn row_count(self) -> u64 {
        self.row_count
    }

    /// 返回按稳定顺序计算的数据集语义 SHA-256。
    #[must_use]
    pub const fn dataset_sha256(self) -> Sha256Digest {
        self.dataset_sha256
    }
}

/// 外部排序失败。
#[derive(Debug)]
pub enum ExternalSortError {
    /// 临时文件系统操作失败。
    Io {
        operation: &'static str,
        path: PathBuf,
        source: std::io::Error,
    },
    /// 规范行载荷无法使用四字节长度编码。
    PayloadLengthOverflow { length: usize },
    /// 排序段中的端点角色字节非法。
    InvalidEndpointRole { value: u8, path: PathBuf },
    /// 排序段结束后仍有未声明字节。
    TrailingRunBytes { path: PathBuf },
    /// 两条记录具有完全相同的合同稳定键。
    DuplicateStableKey { key: StableSortKey },
    /// 输出回调失败。
    Emit(std::io::Error),
    /// 受检查整数运算失败。
    IntegerOverflow(IntegerOverflow),
}

impl Display for ExternalSortError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io {
                operation, path, ..
            } => write!(formatter, "外部排序无法{operation} {}", path.display()),
            Self::PayloadLengthOverflow { length } => {
                write!(formatter, "排序记录载荷长度 {length} 超过 u32")
            }
            Self::InvalidEndpointRole { value, path } => write!(
                formatter,
                "排序段 {} 包含非法端点角色字节 {value}",
                path.display()
            ),
            Self::TrailingRunBytes { path } => {
                write!(formatter, "排序段 {} 包含尾随字节", path.display())
            }
            Self::DuplicateStableKey { .. } => write!(formatter, "完整稳定键重复"),
            Self::Emit(_) => write!(formatter, "无法写出外部排序结果"),
            Self::IntegerOverflow(source) => write!(formatter, "外部排序整数错误：{source}"),
        }
    }
}

impl Error for ExternalSortError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } | Self::Emit(source) => Some(source),
            Self::IntegerOverflow(source) => Some(source),
            Self::PayloadLengthOverflow { .. }
            | Self::InvalidEndpointRole { .. }
            | Self::TrailingRunBytes { .. }
            | Self::DuplicateStableKey { .. } => None,
        }
    }
}

/// 把输入拆成有界排序段，并按完整稳定键执行确定性多路归并。
///
/// 输出回调按最终稳定顺序逐条接收记录，因此调用者无需把完整结果保留在内存。
///
/// # Errors
///
/// 工作目录已存在、排序段读写失败、键重复、长度或计数溢出、输出回调失败时返回错误。
pub fn stable_external_sort<I, F>(
    records: I,
    config: &ExternalSortConfig,
    mut emit: F,
) -> Result<ExternalSortSummary, ExternalSortError>
where
    I: IntoIterator<Item = SortableRecord>,
    F: FnMut(&SortableRecord) -> Result<(), std::io::Error>,
{
    let work_dir = WorkDirectory::create(&config.work_dir)?;
    let mut run_paths = Vec::new();
    let mut run = Vec::with_capacity(config.max_records_per_run.get());

    for record in records {
        run.push(record);
        if run.len() == config.max_records_per_run.get() {
            run_paths.push(write_run(&config.work_dir, run_paths.len(), &mut run)?);
        }
    }
    if !run.is_empty() {
        run_paths.push(write_run(&config.work_dir, run_paths.len(), &mut run)?);
    }

    let mut readers = run_paths
        .iter()
        .map(|path| RunReader::open(path))
        .collect::<Result<Vec<_>, _>>()?;
    let mut heap = BinaryHeap::new();
    for (run_index, reader) in readers.iter_mut().enumerate() {
        if let Some(record) = reader.next_record()? {
            heap.push(HeapRecord { record, run_index });
        }
    }

    let mut previous_key = None;
    let mut semantic_hasher = DatasetSemanticHasher::new();
    while let Some(item) = heap.pop() {
        let key = *item.record.key();
        if previous_key == Some(key) {
            return Err(ExternalSortError::DuplicateStableKey { key });
        }
        let row_hash = sha256(item.record.payload());
        semantic_hasher
            .push(&row_hash)
            .map_err(ExternalSortError::IntegerOverflow)?;
        emit(&item.record).map_err(ExternalSortError::Emit)?;
        previous_key = Some(key);

        if let Some(record) = readers[item.run_index].next_record()? {
            heap.push(HeapRecord {
                record,
                run_index: item.run_index,
            });
        }
    }

    let row_count = semantic_hasher.row_count();
    let dataset_sha256 = semantic_hasher.finalize();
    drop(readers);
    work_dir.cleanup()?;
    Ok(ExternalSortSummary {
        row_count,
        dataset_sha256,
    })
}

struct WorkDirectory {
    path: PathBuf,
    active: bool,
}

impl WorkDirectory {
    fn create(path: &Path) -> Result<Self, ExternalSortError> {
        fs::create_dir(path).map_err(|source| io_error("创建工作目录", path, source))?;
        Ok(Self {
            path: path.to_path_buf(),
            active: true,
        })
    }

    fn cleanup(mut self) -> Result<(), ExternalSortError> {
        fs::remove_dir_all(&self.path)
            .map_err(|source| io_error("清理工作目录", &self.path, source))?;
        self.active = false;
        Ok(())
    }
}

impl Drop for WorkDirectory {
    fn drop(&mut self) {
        if self.active {
            let _ = fs::remove_dir_all(&self.path);
        }
    }
}

fn write_run(
    work_dir: &Path,
    run_index: usize,
    records: &mut Vec<SortableRecord>,
) -> Result<PathBuf, ExternalSortError> {
    records.sort_unstable_by(|left, right| left.key().cmp(right.key()));
    let path = work_dir.join(format!("run-{run_index:020}.bin"));
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .map_err(|source| io_error("创建排序段", &path, source))?;
    let mut writer = BufWriter::new(file);
    write_all(&mut writer, &path, RUN_MAGIC)?;
    let row_count = u64::try_from(records.len()).map_err(|_| {
        ExternalSortError::IntegerOverflow(IntegerOverflow::SortedRowCount)
    })?;
    write_all(&mut writer, &path, &row_count.to_be_bytes())?;
    for record in records.drain(..) {
        write_record(&mut writer, &path, record)?;
    }
    writer
        .flush()
        .map_err(|source| io_error("刷新排序段", &path, source))?;
    Ok(path)
}

fn write_record(
    writer: &mut BufWriter<File>,
    path: &Path,
    record: SortableRecord,
) -> Result<(), ExternalSortError> {
    let (key, payload) = record.into_parts();
    let payload_length = u32::try_from(payload.len()).map_err(|_| {
        ExternalSortError::PayloadLengthOverflow {
            length: payload.len(),
        }
    })?;
    write_all(writer, path, key.protected_endpoint_id())?;
    write_all(writer, path, &key.last_ns().to_be_bytes())?;
    write_all(writer, path, &key.start_ns().to_be_bytes())?;
    write_all(writer, path, key.raw_flow_id())?;
    write_all(writer, path, &[key.endpoint_role_order().as_byte()])?;
    write_all(writer, path, &key.source_row_index().get().to_be_bytes())?;
    write_all(writer, path, &payload_length.to_be_bytes())?;
    write_all(writer, path, &payload)
}

fn write_all(
    writer: &mut BufWriter<File>,
    path: &Path,
    bytes: &[u8],
) -> Result<(), ExternalSortError> {
    writer
        .write_all(bytes)
        .map_err(|source| io_error("写入排序段", path, source))
}

struct RunReader {
    path: PathBuf,
    reader: BufReader<File>,
    remaining: u64,
    end_checked: bool,
}

impl RunReader {
    fn open(path: &Path) -> Result<Self, ExternalSortError> {
        let file = File::open(path).map_err(|source| io_error("打开排序段", path, source))?;
        let mut reader = BufReader::new(file);
        let mut magic = [0u8; 8];
        read_exact(&mut reader, path, &mut magic)?;
        if &magic != RUN_MAGIC {
            return Err(io_error(
                "验证排序段标识",
                path,
                std::io::Error::new(std::io::ErrorKind::InvalidData, "排序段标识不匹配"),
            ));
        }
        let mut count = [0u8; 8];
        read_exact(&mut reader, path, &mut count)?;
        Ok(Self {
            path: path.to_path_buf(),
            reader,
            remaining: u64::from_be_bytes(count),
            end_checked: false,
        })
    }

    fn next_record(&mut self) -> Result<Option<SortableRecord>, ExternalSortError> {
        if self.remaining == 0 {
            if !self.end_checked {
                let mut trailing = [0u8; 1];
                let count = self
                    .reader
                    .read(&mut trailing)
                    .map_err(|source| io_error("检查排序段结尾", &self.path, source))?;
                if count != 0 {
                    return Err(ExternalSortError::TrailingRunBytes {
                        path: self.path.clone(),
                    });
                }
                self.end_checked = true;
            }
            return Ok(None);
        }

        let mut endpoint = [0u8; 32];
        let mut last_ns = [0u8; 8];
        let mut start_ns = [0u8; 8];
        let mut raw_flow = [0u8; 32];
        let mut role = [0u8; 1];
        let mut source_row_index = [0u8; 8];
        let mut payload_length = [0u8; 4];
        read_exact(&mut self.reader, &self.path, &mut endpoint)?;
        read_exact(&mut self.reader, &self.path, &mut last_ns)?;
        read_exact(&mut self.reader, &self.path, &mut start_ns)?;
        read_exact(&mut self.reader, &self.path, &mut raw_flow)?;
        read_exact(&mut self.reader, &self.path, &mut role)?;
        read_exact(&mut self.reader, &self.path, &mut source_row_index)?;
        read_exact(&mut self.reader, &self.path, &mut payload_length)?;
        let role = EndpointRoleOrder::from_byte(role[0]).ok_or_else(|| {
            ExternalSortError::InvalidEndpointRole {
                value: role[0],
                path: self.path.clone(),
            }
        })?;
        let mut payload = vec![0u8; u32::from_be_bytes(payload_length) as usize];
        read_exact(&mut self.reader, &self.path, &mut payload)?;
        self.remaining -= 1;

        Ok(Some(SortableRecord::new(
            StableSortKey::new(
                endpoint,
                i64::from_be_bytes(last_ns),
                i64::from_be_bytes(start_ns),
                raw_flow,
                role,
                SourceRowIndex::new(u64::from_be_bytes(source_row_index)),
            ),
            payload,
        )))
    }
}

fn read_exact(
    reader: &mut BufReader<File>,
    path: &Path,
    bytes: &mut [u8],
) -> Result<(), ExternalSortError> {
    reader
        .read_exact(bytes)
        .map_err(|source| io_error("读取排序段", path, source))
}

struct HeapRecord {
    record: SortableRecord,
    run_index: usize,
}

impl PartialEq for HeapRecord {
    fn eq(&self, other: &Self) -> bool {
        self.record.key() == other.record.key() && self.run_index == other.run_index
    }
}

impl Eq for HeapRecord {}

impl PartialOrd for HeapRecord {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for HeapRecord {
    fn cmp(&self, other: &Self) -> Ordering {
        other
            .record
            .key()
            .cmp(self.record.key())
            .then_with(|| other.run_index.cmp(&self.run_index))
    }
}

fn io_error(
    operation: &'static str,
    path: &Path,
    source: std::io::Error,
) -> ExternalSortError {
    ExternalSortError::Io {
        operation,
        path: path.to_path_buf(),
        source,
    }
}
