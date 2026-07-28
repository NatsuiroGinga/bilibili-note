import pytest

from flow_probe.adapters.base import DatasetSchemaError
from flow_probe.adapters.ciciot import adapt_row as adapt_ciciot
from flow_probe.adapters.genis import adapt_row as adapt_genis
from flow_probe.adapters.hikari import adapt_row as adapt_hikari


def test_genis_adapter_maps_official_fields() -> None:
    row = {
        "BinaryLabel": "0",
        "CategoryLabel": "benign",
        "SubCategoryLabel": "benign",
        "TotPkts": "10",
        "SrcPkts": "6",
        "DstPkts": "4",
        "TotBytes": "1000",
        "sMinPktSz": "40",
        "dMinPktSz": "50",
        "sMaxPktSz": "200",
        "dMaxPktSz": "300",
        "SIntPkt": "2",
        "DIntPkt": "4",
        "Rate": "5",
        "Load": "8000",
    }

    sample = adapt_genis(row, "capture-01.csv", 7)

    assert sample.sample_id == "genis:capture-01.csv:7"
    assert sample.group_id == "capture-01.csv"
    assert sample.binary_label == "benign"
    assert sample.features == {
        "total_packets": 10.0,
        "total_bytes": 1000.0,
        "packet_length_mean": 100.0,
        "packet_length_min": 40.0,
        "packet_length_max": 300.0,
        "iat_mean_ms": 2.75,
        "packet_rate": 5.0,
        "byte_rate": 1000.0,
    }


def test_hikari_adapter_maps_published_fields() -> None:
    row = {
        "uid": "C1",
        "originh": "192.0.2.1",
        "responh": "198.51.100.2",
        "fwd_pkts_tot": "6",
        "bwd_pkts_tot": "4",
        "fwd_pkts_payload.tot": "600",
        "bwd_pkts_payload.tot": "400",
        "flow_pkts_payload.min": "40",
        "flow_pkts_payload.max": "300",
        "flow_pkts_payload.avg": "100",
        "flow_iat.avg": "2000",
        "flow_pkts_per_sec": "5",
        "payload_bytes_per_second": "1000",
        "traffic_category": "Probing",
        "Label": "1",
    }

    sample = adapt_hikari(row, "ALLFLOWMETER_HIKARI2021.csv", 3)

    assert sample.sample_id == "hikari:ALLFLOWMETER_HIKARI2021.csv:3"
    assert sample.group_id.endswith("192.0.2.1->198.51.100.2")
    assert sample.binary_label == "malicious"
    assert sample.attack_family == "Probing"
    assert sample.features["total_packets"] == 10.0
    assert sample.features["total_bytes"] == 1000.0
    assert sample.features["iat_mean_ms"] == 2.0


def test_ciciot_adapter_maps_verified_mirror_fields() -> None:
    row = {
        "Number": 100,
        "Tot sum": 59200,
        "Min": 592,
        "Max": 592,
        "AVG": 592,
        "IAT": 0.000174,
        "Rate": 5779.746173,
        "Label": "BenignTraffic",
        "attack_class": "Benign",
        "label": 0,
    }

    sample = adapt_ciciot(row, "random_3way/train.parquet", 11)

    assert sample.binary_label == "benign"
    assert sample.attack_family == "Benign"
    assert sample.features["iat_mean_ms"] == pytest.approx(0.174)
    assert sample.features["byte_rate"] == pytest.approx(3_421_609.734416)


@pytest.mark.parametrize(
    ("adapter", "row"),
    [
        (adapt_genis, {"BinaryLabel": "unknown"}),
        (adapt_hikari, {"Label": 2}),
        (adapt_ciciot, {"label": "attack"}),
    ],
)
def test_adapters_reject_unknown_labels(adapter, row) -> None:
    with pytest.raises(DatasetSchemaError, match="未知标签"):
        adapter(row, "source.csv", 1)


def test_genis_adapter_reports_missing_required_column() -> None:
    with pytest.raises(DatasetSchemaError, match="缺少必需列.*TotPkts"):
        adapt_genis({"BinaryLabel": 0}, "source.csv", 1)
