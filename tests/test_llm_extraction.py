# tests/test_llm_extraction.py
import json
from pathlib import Path

import pytest

from extractor.extract import extract_drug_label_info as extract

SAMPLES = Path(__file__).parent.parent / "data" / "samples.json"


@pytest.mark.llm
def test_extracts_acne_from_silicea_label():
    # arrange
    data = json.loads(SAMPLES.read_text())
    text = data["samples"][0]["input_text"]

    # act
    result = extract(text)

    # assert
    names = {i.lower().strip() for i in result.indications}
    assert "acne" in names
    assert "boils" in names