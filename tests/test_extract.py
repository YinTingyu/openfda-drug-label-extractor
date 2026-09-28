# tests/test_extract.py
from unittest.mock import patch, MagicMock
from extractor.extract import extract_drug_label_info as extract
from extractor.schema import DrugLabel, SafetyInfo


def make_fake_response(parsed):
    fake = MagicMock()
    fake.output_parsed = parsed
    return fake

@patch("extractor.extract.client")
def test_extract_filters_non_informative_indications(mock_client):
    mock_client.responses.parse.return_value = make_fake_response(
        DrugLabel(indications=["acne", "as directed by the physician"], safety=SafetyInfo())
    )
    result = extract("some label text")
    assert result.indications == ["acne"]

@patch("extractor.extract.client")
def test_extract_uses_temperature_zero(mock_client):
    mock_client.responses.parse.return_value = make_fake_response(DrugLabel(safety=SafetyInfo()))
    extract("some label text")
    kwargs = mock_client.responses.parse.call_args.kwargs
    assert kwargs["temperature"] == 0