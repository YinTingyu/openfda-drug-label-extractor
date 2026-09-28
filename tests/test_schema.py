# tests/test_schema.py
import pytest
from pydantic import ValidationError
from extractor.schema import DrugLabel, SafetyInfo

def test_all_fields_optional_so_model_can_say_nothing():
    label = DrugLabel()
    assert label.indications == []
    assert label.safety.contraindications == []
    assert label.safety.cautions == []
    assert label.safety.stop_use_conditions == []
    assert label.dosage_form is None

def test_dosage_form_rejects_value_outside_enum():
    with pytest.raises(ValidationError):
        DrugLabel(dosage_form="Bark")
