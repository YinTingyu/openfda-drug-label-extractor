# tests/test_extract.py
from unittest.mock import patch, MagicMock
from extractor.extract import extract_drug_label_info as extract
from extractor.schema import DrugLabel, SafetyInfo


def make_fake_response(parsed):
    fake = MagicMock()
    fake.output_parsed = parsed
    return fake

def test_extract_filters_non_informative_indications():
    fake = MagicMock()
    fake.responses.parse.return_value = make_fake_response(
        DrugLabel(indications=["acne", "as directed by the physician"], safety=SafetyInfo())
    )

    result = extract("some label text", client=fake)

    assert result.indications == ["acne"]


def test_extract_uses_temperature_zero():
    fake = MagicMock()
    fake.responses.parse.return_value = make_fake_response(DrugLabel())

    extract("some label text", client=fake)

    assert fake.responses.parse.call_args.kwargs["temperature"] == 0

