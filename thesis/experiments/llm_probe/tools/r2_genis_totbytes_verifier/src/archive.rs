use std::fs::{self, File};
use std::io::{BufReader, Read};
use std::path::{Component, Path};

use anyhow::{Context, Result, bail, ensure};
use md5::Md5;
use sha2::{Digest, Sha256};

use crate::model::ArtifactDigest;

pub const OFFICIAL_PACKET_ARCHIVE_SIZE: u64 = 1_028_741_083;
pub const OFFICIAL_PACKET_ARCHIVE_MD5: &str = "5afbceaadfe3c3476f54723434d59b4a";
pub const OFFICIAL_FLOW_ARCHIVE_SIZE: u64 = 380_755_720;
pub const OFFICIAL_FLOW_ARCHIVE_MD5: &str = "063b7a2ec6e6b73cc302151d2b3ba6d7";
pub const OFFICIAL_FLOW_ARCHIVE_SHA256: &str =
    "72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30";

pub fn validate_sha256(value: &str, field_name: &str) -> Result<()> {
    ensure!(
        value.len() == 64
            && value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
        "{field_name} 必须是 64 位小写十六进制 SHA-256"
    );
    Ok(())
}

pub fn validate_revision(value: &str) -> Result<()> {
    let valid_length = matches!(value.len(), 40 | 64);
    ensure!(
        valid_length
            && value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
        "tool_revision 必须是 40 或 64 位小写十六进制不可变标识"
    );
    Ok(())
}

pub fn ensure_regular_file(path: &Path, role: &str) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .with_context(|| format!("无法读取{role}元数据：{}", path.display()))?;
    ensure!(!metadata.file_type().is_symlink(), "{role}不得是符号链接");
    ensure!(metadata.is_file(), "{role}必须是普通文件");
    Ok(())
}

pub fn hash_file(path: &Path) -> Result<ArtifactDigest> {
    ensure_regular_file(path, "输入文件")?;
    let source = File::open(path).with_context(|| format!("无法打开输入：{}", path.display()))?;
    let mut reader = BufReader::with_capacity(8 * 1024 * 1024, source);
    let mut sha256 = Sha256::new();
    let mut md5 = Md5::new();
    let mut size_bytes = 0_u64;
    let mut buffer = vec![0_u8; 8 * 1024 * 1024];
    loop {
        let read = reader
            .read(&mut buffer)
            .with_context(|| format!("读取输入失败：{}", path.display()))?;
        if read == 0 {
            break;
        }
        size_bytes = size_bytes
            .checked_add(u64::try_from(read).context("输入块大小无法转换为 u64")?)
            .context("输入大小发生整数溢出")?;
        sha256.update(&buffer[..read]);
        md5.update(&buffer[..read]);
    }
    Ok(ArtifactDigest {
        size_bytes,
        md5: hex::encode(md5.finalize()),
        sha256: hex::encode(sha256.finalize()),
    })
}

pub fn verify_digest(
    digest: &ArtifactDigest,
    expected_size: Option<u64>,
    expected_md5: Option<&str>,
    expected_sha256: &str,
    role: &str,
) -> Result<()> {
    if let Some(size) = expected_size {
        ensure!(digest.size_bytes == size, "{role}精确大小不一致");
    }
    if let Some(md5) = expected_md5 {
        ensure!(digest.md5 == md5, "{role}官方 MD5 不一致");
    }
    ensure!(digest.sha256 == expected_sha256, "{role} SHA-256 不一致");
    Ok(())
}

pub fn validate_member_path(value: &str, role: &str) -> Result<()> {
    ensure!(!value.is_empty(), "{role}成员路径不能为空");
    ensure!(!value.contains('\\') && !value.contains('\0'), "{role}成员路径含非法字符");
    let path = Path::new(value);
    ensure!(!path.is_absolute(), "{role}成员路径不得是绝对路径");
    for component in path.components() {
        match component {
            Component::Normal(_) => {}
            _ => bail!("{role}成员路径含不安全分量"),
        }
    }
    Ok(())
}

pub fn sha256_bytes(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

pub struct DigestReader<R> {
    inner: R,
    sha256: Sha256,
    size_bytes: u64,
}

impl<R> DigestReader<R> {
    pub fn new(inner: R) -> Self {
        Self {
            inner,
            sha256: Sha256::new(),
            size_bytes: 0,
        }
    }

    pub fn finish(self) -> Result<(u64, String)> {
        Ok((self.size_bytes, hex::encode(self.sha256.finalize())))
    }
}

impl<R: Read> Read for DigestReader<R> {
    fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
        let read = self.inner.read(buffer)?;
        if read > 0 {
            self.size_bytes = self
                .size_bytes
                .checked_add(u64::try_from(read).map_err(std::io::Error::other)?)
                .ok_or_else(|| std::io::Error::other("成员大小发生整数溢出"))?;
            self.sha256.update(&buffer[..read]);
        }
        Ok(read)
    }
}
