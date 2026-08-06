use lspr24_g0::{
    CanonicalValue, IntegerOverflow, SourceRowIndex, dataset_semantic_hash, sha256,
    tuple_encode,
};

const VECTORS: &str = include_str!(
    "../../../tests/fixtures/lspr24_g0/canonical_vectors.json"
);

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

fn mixed_tuple() -> Vec<CanonicalValue<'static>> {
    vec![
        CanonicalValue::Null,
        CanonicalValue::Bool(true),
        CanonicalValue::I64(-2),
        CanonicalValue::U16(0x1234),
        CanonicalValue::Utf8("Aé"),
        CanonicalValue::Bytes(&[0x00, 0xff]),
    ]
}

fn second_row() -> Vec<CanonicalValue<'static>> {
    vec![
        CanonicalValue::Utf8(""),
        CanonicalValue::Null,
        CanonicalValue::Bool(false),
        CanonicalValue::U64(1),
        CanonicalValue::FixedDecimal12(-1),
    ]
}

#[test]
fn shared_vectors_fix_tuple_bytes_row_hashes_and_ordered_dataset_hash() {
    let first_encoded = tuple_encode(&mixed_tuple()).expect("规范人工元组应可编码");
    let second_encoded = tuple_encode(&second_row()).expect("第二个人工元组应可编码");
    let first_hash = sha256(&first_encoded);
    let second_hash = sha256(&second_encoded);

    assert_eq!(encode_hex(&first_encoded), fixture_value("mixed_tuple_hex"));
    assert_eq!(encode_hex(&first_hash), fixture_value("mixed_tuple_sha256"));
    assert_eq!(encode_hex(&second_encoded), fixture_value("second_row_hex"));
    assert_eq!(encode_hex(&second_hash), fixture_value("second_row_sha256"));
    assert_eq!(
        encode_hex(&dataset_semantic_hash(&[first_hash, second_hash])),
        fixture_value("ordered_dataset_sha256")
    );
    assert_eq!(
        encode_hex(&dataset_semantic_hash(&[second_hash, first_hash])),
        fixture_value("reversed_dataset_sha256")
    );
}

#[test]
fn null_empty_string_integer_width_and_row_order_are_distinct() {
    assert_ne!(
        tuple_encode(&[CanonicalValue::Null]).expect("空值应可编码"),
        tuple_encode(&[CanonicalValue::Utf8("")]).expect("空字符串应可编码")
    );
    assert_ne!(
        tuple_encode(&[CanonicalValue::U8(1)]).expect("八位整数应可编码"),
        tuple_encode(&[CanonicalValue::U16(1)]).expect("十六位整数应可编码")
    );

    let first = sha256(b"first");
    let second = sha256(b"second");
    assert_ne!(
        dataset_semantic_hash(&[first, second]),
        dataset_semantic_hash(&[second, first])
    );
}

#[test]
fn source_row_index_increment_fails_instead_of_wrapping() {
    let error = SourceRowIndex::new(u64::MAX)
        .checked_next()
        .expect_err("最大源行号继续递增必须失败");

    assert_eq!(error, IntegerOverflow::SourceRowIndex);
}
