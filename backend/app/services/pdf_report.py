"""Generate a complete PDF report for stored textile waste batches."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _display(value: object) -> str:
    if value is None or value == "":
        return "Not provided"
    return escape(str(value)).replace("\n", "<br/>")


def _label(value: object) -> str:
    return str(value).replace("_", " ").strip().title()


def _flatten_analysis(value: object, prefix: str = "") -> list[tuple[str, object]]:
    if isinstance(value, dict):
        rows: list[tuple[str, object]] = []
        for key, nested_value in value.items():
            nested_label = f"{prefix} - {_label(key)}" if prefix else _label(key)
            rows.extend(_flatten_analysis(nested_value, nested_label))
        return rows
    if isinstance(value, list):
        if not value:
            return [(prefix or "Result", "None")]
        rows = []
        for index, nested_value in enumerate(value, start=1):
            item_label = f"{prefix} {index}" if prefix else f"Item {index}"
            rows.extend(_flatten_analysis(nested_value, item_label))
        return rows
    return [(prefix or "Result", value)]


def _analysis_rows(value: str | None) -> list[tuple[str, object]]:
    if not value:
        return [("Analysis", "No analysis results saved for this batch.")]
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = value
    return _flatten_analysis(parsed)


def _sustainability_rows(batch: object) -> list[tuple[str, object]]:
    assessment = getattr(batch, "assessment", None)
    if assessment is None:
        return [("Sustainability assessment", "Not calculated for this batch.")]
    fields = (
        ("Assessed quantity", "quantity_kg", " kg"),
        ("CO2 saved", "co2_saved_kg", " kg CO2e"),
        ("Water saved", "water_saved_litres", " litres"),
        ("Landfill reduction", "landfill_reduction_kg", " kg"),
        ("Recoverable material", "recoverable_material_kg", " kg"),
        ("Recyclability score", "recyclability_score", "/100"),
        ("Reuse score", "reuse_score", "/100"),
        ("Sustainability score", "sustainability_score", "/100"),
        ("Material recovery score", "material_recovery_score", "/100"),
        ("Circularity score", "circularity_score", "/100"),
        ("Circularity category", "circularity_category", ""),
        ("Recommended action", "recommended_action", ""),
        ("Processing method", "recommended_processing_method", ""),
    )
    rows = []
    for label, attribute, suffix in fields:
        value = getattr(assessment, attribute, None)
        rows.append((label, f"{value}{suffix}" if value not in (None, "") else "Not available"))
    return rows


def _draw_page(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "Textile Circularity Platform")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_waste_report(items: Iterable[object]) -> bytes:
    batches = list(items)
    is_single_batch = len(batches) == 1
    report_title = "Waste Batch Details" if is_single_batch else "Complete Textile Waste Report"
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=report_title,
        author="Textile Circularity Platform",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#0F172A"),
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportSubtitle",
            parent=styles["BodyText"],
            textColor=colors.HexColor("#475569"),
            fontSize=9.5,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "HeaderLabel",
            parent=styles["BodyText"],
            textColor=colors.white,
            fontSize=8.5,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            "BatchTitle",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0E7490"),
            fontSize=15,
            leading=19,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "FieldValue",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A"),
        )
    )
    styles.add(
        ParagraphStyle(
            "SmallText",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )
    )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_counts = Counter(getattr(batch, "status", None) or "Unspecified" for batch in batches)
    story = [
        Table(
            [[Paragraph("TEXTILE CIRCULARITY PLATFORM", styles["HeaderLabel"])]],
            colWidths=[165 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        ),
        Spacer(1, 7 * mm),
        Paragraph(report_title, styles["ReportTitle"]),
    ]

    if not is_single_batch:
        story.extend(
            [
                Paragraph(
                    "A clear record of the registered textile waste information shown line by line.",
                    styles["ReportSubtitle"],
                ),
                Paragraph(f"Generated: {generated}", styles["ReportSubtitle"]),
                Table(
                    [
                        [Paragraph("<b>Total registered batches</b>", styles["SmallText"]), Paragraph(str(len(batches)), styles["FieldValue"])],
                        [Paragraph("<b>Status summary</b>", styles["SmallText"]), Paragraph(_display(", ".join(f"{key}: {value}" for key, value in sorted(status_counts.items()))), styles["FieldValue"])],
                    ],
                    colWidths=[52 * mm, 113 * mm],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#CFFAFE")),
                            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F8FAFC")),
                            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#94A3B8")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    ),
                ),
                Spacer(1, 7 * mm),
            ]
        )
    else:
        story.append(Spacer(1, 2 * mm))

    if not batches:
        story.append(Paragraph("No waste batches are currently stored.", styles["BodyText"]))

    fields = (
        ("Batch number", "waste_batch_id"),
        ("Database ID", "id"),
        ("Fabric type", "fabric_type"),
        ("Source", "source"),
        ("Quantity", "quantity"),
        ("Color", "color"),
        ("Condition", "condition"),
        ("Collection date", "collection_date"),
        ("Status", "status"),
        ("Uploaded by", "uploaded_by"),
        ("Assigned to", "assigned_to"),
        ("Image URL", "image_url"),
    )
    for index, batch in enumerate(batches):
        if index and index % 3 == 0:
            story.append(PageBreak())
        batch_id = getattr(batch, "waste_batch_id", None) or f"Batch {index + 1}"
        story.append(Paragraph(f"Batch: {_display(batch_id)}", styles["BatchTitle"]))
        rows = [
            [Paragraph(f"<b>{escape(label)}</b>", styles["SmallText"]), Paragraph(_display(getattr(batch, attribute, None)), styles["SmallText"])]
            for label, attribute in fields
        ]
        story.append(
            Table(
                rows,
                colWidths=[52 * mm, 113 * mm],
                repeatRows=0,
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECFEFF")),
                        ("BACKGROUND", (1, 0), (1, -1), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#94A3B8")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            )
        )
        analysis_rows = [
            [
                Paragraph(f"<b>{escape(label)}</b>", styles["SmallText"]),
                Paragraph(_display(value), styles["FieldValue"]),
            ]
            for label, value in _analysis_rows(getattr(batch, "analysis_results", None))
        ]
        story.extend(
            [
                Spacer(1, 5 * mm),
                Paragraph("Saved analysis results", styles["BatchTitle"]),
                Table(
                    analysis_rows,
                    colWidths=[64 * mm, 101 * mm],
                    repeatRows=0,
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0FDFA")),
                            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F8FAFC")),
                            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#94A3B8")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 7),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ]
                    ),
                ),
                Spacer(1, 6 * mm),
            ]
        )
        sustainability_rows = [
            [Paragraph(f"<b>{escape(label)}</b>", styles["SmallText"]), Paragraph(_display(value), styles["FieldValue"])]
            for label, value in _sustainability_rows(batch)
        ]
        story.extend(
            [
                Paragraph("Sustainability intelligence", styles["BatchTitle"]),
                Table(
                    sustainability_rows,
                    colWidths=[64 * mm, 101 * mm],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECFDF5")),
                            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F8FAFC")),
                            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#94A3B8")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 7),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ]
                    ),
                ),
                Spacer(1, 6 * mm),
            ]
        )

    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return output.getvalue()
