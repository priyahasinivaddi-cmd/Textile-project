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


def _analysis_text(value: str | None) -> str:
    if not value:
        return "No analysis results saved for this batch."
    try:
        parsed = json.loads(value)
        value = json.dumps(parsed, indent=2, ensure_ascii=True)
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return _display(value)


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
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Complete Textile Waste Report",
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
            "SmallText",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )
    )
    styles.add(
        ParagraphStyle(
            "AnalysisText",
            parent=styles["BodyText"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#334155"),
        )
    )

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_counts = Counter(getattr(batch, "status", None) or "Unspecified" for batch in batches)
    story = [
        Paragraph("Complete Textile Waste Report", styles["ReportTitle"]),
        Paragraph(f"Generated: {generated}", styles["SmallText"]),
        Spacer(1, 5 * mm),
        Table(
            [
                [Paragraph("Total batches", styles["SmallText"]), Paragraph(str(len(batches)), styles["SmallText"])],
                [Paragraph("Status summary", styles["SmallText"]), Paragraph(_display(", ".join(f"{key}: {value}" for key, value in sorted(status_counts.items()))), styles["SmallText"])],
            ],
            colWidths=[40 * mm, 125 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECFEFF")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 6 * mm),
    ]

    if not batches:
        story.append(Paragraph("No waste batches are currently stored.", styles["BodyText"]))

    fields = (
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
                colWidths=[40 * mm, 125 * mm],
                repeatRows=0,
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                ),
            )
        )
        story.extend(
            [
                Spacer(1, 3 * mm),
                Paragraph("<b>Saved analysis results</b>", styles["SmallText"]),
                Spacer(1, 1.5 * mm),
                Paragraph(_analysis_text(getattr(batch, "analysis_results", None)), styles["AnalysisText"]),
                Spacer(1, 6 * mm),
            ]
        )

    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return output.getvalue()
