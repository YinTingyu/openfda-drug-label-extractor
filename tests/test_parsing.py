# tests/test_parsing.py
from extractor.parsing import field_to_text, get_drug_name, label_to_text

def test_field_to_text_handles_list():
    assert field_to_text(["a", "b"]) == "a b"

def test_field_to_text_handles_string_without_splitting_chars():
    # 回归测试：曾经把 "20210902" 变成 "2 0 2 1 0 9 0 2"
    assert field_to_text("20210902") == "20210902"


def test_field_to_text_handles_dict():
    assert field_to_text({"brand_name": ["X"]}) == "brand_name: X"

def test_get_drug_name_falls_back_to_brand_name():
    label = {"openfda": {"brand_name": ["Betadine"]}}
    assert get_drug_name(label) == "Betadine"

def test_get_drug_name_returns_none_when_openfda_empty():
    assert get_drug_name({"openfda": {}}) is None

def test_get_drug_name_returns_none_when_openfda_missing():
    assert get_drug_name({}) is None

def test_get_drug_name_keeps_all_names_for_combination_products():
    label = {"openfda": {"generic_name": ["A", "B", "C"]}}
    assert get_drug_name(label) == "A, B, C"


def test_label_to_text_excludes_irrelevant_sections():
    label = {
        "indications_and_usage": ["treats acne"],
        "spl_product_data_elements": ["DAPHNE MEZEREUM BARK"],
    }
    text = label_to_text(label)
    assert "acne" in text
    assert "BARK" not in text   # 回归测试：曾经污染 dosage_form