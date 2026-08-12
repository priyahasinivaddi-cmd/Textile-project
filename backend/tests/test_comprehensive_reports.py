import pytest
from fastapi import HTTPException

from app.routes.comprehensive_reports import REPORTS, _validate


def test_all_required_dedicated_reports_are_registered():
    assert set(REPORTS) == {
        "waste-classification",
        "recycling",
        "environmental-impact",
        "circular-economy",
        "esg",
    }
    assert all(report["title"] and report["columns"] for report in REPORTS.values())


def test_unknown_report_type_is_rejected():
    with pytest.raises(HTTPException) as error:
        _validate("unknown")
    assert error.value.status_code == 404
