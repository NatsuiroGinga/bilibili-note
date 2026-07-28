from flow_probe.schemas import CANONICAL_CORE_FIELDS, FlowSample
from flow_probe.serialize import serialize_flow


def make_sample() -> FlowSample:
    features = {field: None for field in CANONICAL_CORE_FIELDS}
    features.update(
        {
            "total_packets": 10.0,
            "total_bytes": 1000.0,
            "packet_length_mean": 100.1256789,
            "packet_length_min": 40.0,
            "packet_length_max": 300.0,
            "iat_mean_ms": 2.75,
            "packet_rate": 5.0,
        }
    )
    return FlowSample(
        sample_id="genis:capture.csv:7",
        source_dataset="genis",
        source_file="capture.csv",
        group_id="capture.csv",
        original_label="recon-dns",
        binary_label="malicious",
        attack_family="recon",
        feature_view="canonical_core_v1",
        features=features,
    )


def test_serialize_flow_uses_fixed_order_and_numeric_format() -> None:
    text = serialize_flow(make_sample())

    feature_line = text.splitlines()[1]
    assert feature_line == (
        "流量：total_packets=10;total_bytes=1000;packet_length_mean=100.126;"
        "packet_length_min=40;packet_length_max=300;iat_mean_ms=2.75;"
        "packet_rate=5;byte_rate=NA"
    )


def test_serialize_flow_does_not_leak_sample_metadata() -> None:
    text = serialize_flow(make_sample())

    for forbidden in ("genis", "capture.csv", "recon-dns", "sample_id", "source_dataset"):
        assert forbidden not in text


def test_serialize_flow_is_deterministic() -> None:
    sample = make_sample()

    assert serialize_flow(sample) == serialize_flow(sample)
