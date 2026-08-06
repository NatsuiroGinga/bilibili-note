//! 时间列扫描的资源配置。

use std::num::NonZeroUsize;

/// 正式扫描采用的默认批大小。
pub const DEFAULT_BATCH_SIZE: usize = 65_536;

/// Parquet 时间列扫描配置。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScanConfig {
    batch_size: NonZeroUsize,
}

impl ScanConfig {
    /// 使用非零批大小创建扫描配置。
    #[must_use]
    pub const fn new(batch_size: NonZeroUsize) -> Self {
        Self { batch_size }
    }

    /// 返回每个 Arrow 批允许包含的最大行数。
    #[must_use]
    pub const fn batch_size(self) -> usize {
        self.batch_size.get()
    }
}

impl Default for ScanConfig {
    fn default() -> Self {
        Self::new(
            NonZeroUsize::new(DEFAULT_BATCH_SIZE).expect("固定默认批大小必须大于零"),
        )
    }
}
