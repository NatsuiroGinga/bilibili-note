//! 不覆盖正式路径和同目录暂存路径的输出发布。

use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::{self, File, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

/// 排他输出创建或发布失败。
#[derive(Debug)]
pub enum OutputError {
    /// 正式路径或固定 `.partial` 路径已经存在。
    AlreadyExists(PathBuf),
    /// 文件系统操作失败。
    Io {
        /// 操作涉及的路径。
        path: PathBuf,
        /// 底层输入输出错误。
        source: io::Error,
    },
}

impl Display for OutputError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::AlreadyExists(path) => write!(formatter, "输出路径已存在：{}", path.display()),
            Self::Io { path, source } => {
                write!(formatter, "输出路径 {} 操作失败：{source}", path.display())
            }
        }
    }
}

impl Error for OutputError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::AlreadyExists(_) => None,
            Self::Io { source, .. } => Some(source),
        }
    }
}

/// 同目录排他暂存输出。
///
/// 正式路径和 `<正式路径>.partial` 均必须在创建时不存在。发布使用硬链接的
/// 排他目录项创建语义，目标已存在时不会被替换。
#[derive(Debug)]
pub struct PartialOutput {
    formal_path: PathBuf,
    partial_path: PathBuf,
    file: Option<File>,
    formal_created: bool,
    published: bool,
}

/// 排他发布中可注入并观察的发布后阶段。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CommitStage {
    /// 正式硬链接建立后、删除暂存目录项前。
    RemovePartial,
    /// 暂存目录项删除后、刷新父目录前。
    SyncParent,
}

/// 发布后文件系统阶段的可替换操作边界。
pub trait PostPublishOperations {
    /// 在指定阶段执行前返回结果；错误会触发正式与暂存目录项回滚。
    fn before_operation(&self, stage: CommitStage) -> io::Result<()>;
}

/// 生产环境不注入故障的发布后操作。
#[derive(Debug, Clone, Copy, Default)]
pub struct SystemPostPublishOperations;

impl PostPublishOperations for SystemPostPublishOperations {
    fn before_operation(&self, _stage: CommitStage) -> io::Result<()> {
        Ok(())
    }
}

impl PartialOutput {
    /// 为正式路径排他创建固定同目录 `.partial` 文件。
    ///
    /// # Errors
    ///
    /// 正式路径或暂存路径已存在，或文件系统操作失败时返回错误。
    pub fn create(formal_path: impl AsRef<Path>) -> Result<Self, OutputError> {
        let formal_path = formal_path.as_ref().to_path_buf();
        reject_existing(&formal_path)?;
        let partial_path = append_partial_suffix(&formal_path);
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&partial_path)
            .map_err(|source| map_create_error(&partial_path, source))?;

        Ok(Self {
            formal_path,
            partial_path,
            file: Some(file),
            formal_created: false,
            published: false,
        })
    }

    /// 返回暂存路径。
    #[must_use]
    pub fn partial_path(&self) -> &Path {
        &self.partial_path
    }

    /// 向暂存文件追加全部字节。
    ///
    /// # Errors
    ///
    /// 写入失败时返回底层输入输出错误。
    pub fn write_all(&mut self, bytes: &[u8]) -> Result<(), OutputError> {
        let file = self.file.as_mut().ok_or_else(|| OutputError::Io {
            path: self.partial_path.clone(),
            source: io::Error::other("暂存文件已经关闭"),
        })?;
        file.write_all(bytes).map_err(|source| OutputError::Io {
            path: self.partial_path.clone(),
            source,
        })
    }

    /// 刷新暂存文件并以不覆盖语义发布到正式路径。
    ///
    /// # Errors
    ///
    /// 刷新、排他发布、删除暂存目录项或刷新父目录失败时返回错误。
    pub fn commit(mut self) -> Result<PathBuf, OutputError> {
        self.commit_inner(&SystemPostPublishOperations)
    }

    /// 使用显式发布后操作完成排他发布。
    ///
    /// 该入口用于文件系统故障边界和可替换的生产存储实现。任一发布后阶段失败时，
    /// 析构路径都会删除本次创建的正式目录项和暂存目录项。
    pub fn commit_with_operations(
        mut self,
        operations: &impl PostPublishOperations,
    ) -> Result<PathBuf, OutputError> {
        self.commit_inner(operations)
    }

    fn commit_inner(
        &mut self,
        operations: &impl PostPublishOperations,
    ) -> Result<PathBuf, OutputError> {
        let file = self.file.take().ok_or_else(|| OutputError::Io {
            path: self.partial_path.clone(),
            source: io::Error::other("暂存文件已经关闭"),
        })?;
        file.sync_all().map_err(|source| OutputError::Io {
            path: self.partial_path.clone(),
            source,
        })?;
        drop(file);

        fs::hard_link(&self.partial_path, &self.formal_path)
            .map_err(|source| map_create_error(&self.formal_path, source))?;
        self.formal_created = true;
        operations
            .before_operation(CommitStage::RemovePartial)
            .map_err(|source| OutputError::Io {
                path: self.partial_path.clone(),
                source,
            })?;
        fs::remove_file(&self.partial_path).map_err(|source| OutputError::Io {
            path: self.partial_path.clone(),
            source,
        })?;
        operations
            .before_operation(CommitStage::SyncParent)
            .map_err(|source| OutputError::Io {
                path: self.formal_path.clone(),
                source,
            })?;
        sync_parent_directory(&self.formal_path)?;
        self.published = true;
        Ok(self.formal_path.clone())
    }
}

impl Drop for PartialOutput {
    fn drop(&mut self) {
        if !self.published {
            if self.formal_created {
                let _ = fs::remove_file(&self.formal_path);
            }
            let _ = fs::remove_file(&self.partial_path);
        }
    }
}

fn append_partial_suffix(formal_path: &Path) -> PathBuf {
    let mut value = formal_path.as_os_str().to_os_string();
    value.push(".partial");
    PathBuf::from(value)
}

fn reject_existing(path: &Path) -> Result<(), OutputError> {
    match fs::symlink_metadata(path) {
        Ok(_) => Err(OutputError::AlreadyExists(path.to_path_buf())),
        Err(source) if source.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(OutputError::Io {
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn map_create_error(path: &Path, source: io::Error) -> OutputError {
    if source.kind() == io::ErrorKind::AlreadyExists {
        OutputError::AlreadyExists(path.to_path_buf())
    } else {
        OutputError::Io {
            path: path.to_path_buf(),
            source,
        }
    }
}

fn sync_parent_directory(path: &Path) -> Result<(), OutputError> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    let directory = File::open(parent).map_err(|source| OutputError::Io {
        path: parent.to_path_buf(),
        source,
    })?;
    directory.sync_all().map_err(|source| OutputError::Io {
        path: parent.to_path_buf(),
        source,
    })
}
