use std::num::NonZeroUsize;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

use lspr24_g0::{
    EndpointRoleOrder, ExternalSortConfig, ExternalSortError, SortableRecord, SourceRowIndex,
    StableSortKey, stable_external_sort,
};

const VECTORS: &str = include_str!(
    "../../../tests/fixtures/lspr24_g0/canonical_vectors.json"
);
static NEXT_WORK_ID: AtomicU64 = AtomicU64::new(0);

fn fixture_value(key: &str) -> &str {
    let prefix = format!("\"{key}\": \"");
    VECTORS
        .lines()
        .find_map(|line| {
            let value = line.trim().strip_prefix(&prefix)?;
            value
                .strip_suffix("\",")
                .or_else(|| value.strip_suffix('\"'))
        })
        .unwrap_or_else(|| panic!("共享规范向量缺少字段 {key}"))
}

fn encode_hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        encoded.push(char::from(DIGITS[usize::from(byte >> 4)]));
        encoded.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    encoded
}

fn record(
    payload: u8,
    endpoint: u8,
    last_ns: i64,
    start_ns: i64,
    raw_flow: u8,
    role: EndpointRoleOrder,
    source_row_index: u64,
) -> SortableRecord {
    SortableRecord::new(
        StableSortKey::new(
            [endpoint; 32],
            last_ns,
            start_ns,
            [raw_flow; 32],
            role,
            SourceRowIndex::new(source_row_index),
        ),
        vec![payload],
    )
}

fn artificial_records() -> Vec<SortableRecord> {
    vec![
        record(0x10, 0, 99, 1, 9, EndpointRoleOrder::Destination, 9),
        record(0x20, 1, 9, 1, 9, EndpointRoleOrder::Destination, 9),
        record(0x30, 1, 10, 0, 9, EndpointRoleOrder::Destination, 9),
        record(0x40, 1, 10, 1, 0, EndpointRoleOrder::Destination, 9),
        record(0x50, 1, 10, 1, 1, EndpointRoleOrder::Source, 3),
        record(0x60, 1, 10, 1, 1, EndpointRoleOrder::Source, 4),
        record(0x70, 1, 10, 1, 1, EndpointRoleOrder::Destination, 1),
        record(0x80, 2, -99, -100, 0, EndpointRoleOrder::Source, 0),
    ]
}

fn unique_work_dir(label: &str) -> PathBuf {
    let id = NEXT_WORK_ID.fetch_add(1, Ordering::Relaxed);
    std::env::temp_dir().join(format!(
        "lspr24-g0-sort-{}-{id}-{label}",
        std::process::id()
    ))
}

fn sort_payloads(
    records: Vec<SortableRecord>,
    run_size: usize,
    label: &str,
) -> (Vec<u8>, u64, [u8; 32]) {
    let work_dir = unique_work_dir(label);
    let config = ExternalSortConfig::new(
        &work_dir,
        NonZeroUsize::new(run_size).expect("测试排序段大小必须非零"),
    );
    let mut payloads = Vec::new();
    let summary = stable_external_sort(records, &config, |record| {
        payloads.extend_from_slice(record.payload());
        Ok::<(), std::io::Error>(())
    })
    .expect("有效人工记录应能完成外部排序");

    assert!(!work_dir.exists(), "成功归并后必须清理本次排序工作目录");
    (payloads, summary.row_count(), summary.dataset_sha256())
}

#[test]
fn complete_key_orders_every_field_and_run_size_does_not_change_output() {
    let records = artificial_records();
    let scrambled = vec![
        records[6].clone(),
        records[2].clone(),
        records[7].clone(),
        records[4].clone(),
        records[0].clone(),
        records[5].clone(),
        records[1].clone(),
        records[3].clone(),
    ];
    let reversed = scrambled.iter().rev().cloned().collect::<Vec<_>>();

    let one = sort_payloads(scrambled.clone(), 1, "one");
    let three = sort_payloads(reversed, 3, "three");
    let oversized = sort_payloads(scrambled, 65_536, "oversized");

    assert_eq!(one.0, vec![0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]);
    assert_eq!(one.1, 8);
    assert_eq!(encode_hex(&one.2), fixture_value("stable_sort_dataset_sha256"));
    assert_eq!(three, one);
    assert_eq!(oversized, one);
}

#[test]
fn duplicate_complete_key_is_rejected_instead_of_using_run_layout_as_tie_breaker() {
    let duplicate = record(0xaa, 1, 2, 1, 3, EndpointRoleOrder::Source, 4);
    let work_dir = unique_work_dir("duplicate");
    let config = ExternalSortConfig::new(
        &work_dir,
        NonZeroUsize::new(1).expect("测试排序段大小必须非零"),
    );
    let error = stable_external_sort(
        vec![duplicate.clone(), duplicate],
        &config,
        |_| Ok::<(), std::io::Error>(()),
    )
    .expect_err("重复完整稳定键必须失败");

    assert!(matches!(error, ExternalSortError::DuplicateStableKey { .. }));
    assert!(!work_dir.exists(), "失败后也必须清理本次排序工作目录");
}
