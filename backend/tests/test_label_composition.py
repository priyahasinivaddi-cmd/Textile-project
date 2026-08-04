import pytest

from app.services.label_composition import parse_label_composition


def test_single_fibre_label():
    result = parse_label_composition("100% Cotton")
    assert result["fabric_type"] == "Cotton"
    assert result["blend_type"] == "single"
    assert result["evidence_source"] == "care_label"


def test_mixed_label_and_aliases():
    result = parse_label_composition("70% viscose, 30% polyamide")
    assert result["fabric_type"] == "Mixed Fabrics"
    assert result["fiber_composition"] == "70.0% Rayon / 30.0% Nylon"


def test_invalid_total_is_rejected():
    with pytest.raises(ValueError, match="total about 100%"):
        parse_label_composition("40% Cotton, 20% Polyester")
