import pytest

from flow_probe.output_parser import parse_prediction


@pytest.mark.parametrize("label", ["benign", "malicious"])
def test_parse_prediction_accepts_exact_label_object(label: str) -> None:
    result = parse_prediction(f'  {{"label":"{label}"}}\n')

    assert result.is_valid is True
    assert result.label == label
    assert result.error is None


@pytest.mark.parametrize(
    "text",
    [
        '结果是 {"label":"benign"}',
        '```json\n{"label":"benign"}\n```',
        '{"label":"benign","reason":"正常"}',
        '{"label":"attack"}',
        '{"label":"benign"',
        '[{"label":"benign"}]',
    ],
)
def test_parse_prediction_rejects_non_exact_output(text: str) -> None:
    result = parse_prediction(text)

    assert result.is_valid is False
    assert result.label is None
    assert result.error
