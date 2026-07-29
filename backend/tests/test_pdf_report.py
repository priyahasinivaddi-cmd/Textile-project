import json
from io import BytesIO
from types import SimpleNamespace

import pdfplumber

from app.services.pdf_report import build_waste_report


def test_single_batch_pdf_lists_waste_details():
    batch = SimpleNamespace(
        id=7,
        waste_batch_id="WB-TEST-007",
        fabric_type="Cotton",
        source="Unit 3",
        quantity="125 kg",
        color="Blue",
        condition="Recyclable",
        collection_date="2026-07-29",
        status="Collected",
        uploaded_by="Manufacturer",
        assigned_to="Recycling Facility",
        image_url=None,
        analysis_results=json.dumps(
            {
                "material": {
                    "fabric_type": "Cotton",
                    "confidence": "96%",
                },
                "waste_classification": {
                    "category": "Recyclable",
                    "quality": "Good",
                },
                "recommendations": [
                    "Send for fibre recovery",
                    "Keep the batch dry",
                ],
            }
        ),
    )

    pdf_bytes = build_waste_report([batch])

    assert pdf_bytes.startswith(b"%PDF")
    with pdfplumber.open(BytesIO(pdf_bytes)) as report:
        text = "\n".join(page.extract_text() or "" for page in report.pages)

    assert "Waste Batch Details" in text
    assert "Batch number" in text
    assert "WB-TEST-007" in text
    assert "Cotton" in text
    assert "125 kg" in text
    assert "Collected" in text
    assert "Total registered batches" not in text
    assert "Material - Fabric Type" in text
    assert "96%" in text
    assert "Waste Classification - Category" in text
    assert "Recommendations 1" in text
    assert "Send for fibre recovery" in text
