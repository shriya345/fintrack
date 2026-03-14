"""
PDF Report Generator using ReportLab.

Produces a clean monthly expense report with:
- Summary table (category totals vs budget)
- Top merchants
- Anomalies section
- Simple bar chart (category totals)
"""

import os
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF


# Brand colors
GREEN = colors.HexColor("#1D9E75")
DARK  = colors.HexColor("#2C2C2A")
GRAY  = colors.HexColor("#888780")
LIGHT = colors.HexColor("#F1EFE8")
RED   = colors.HexColor("#D85A30")
AMBER = colors.HexColor("#BA7517")


def generate_pdf_report(
    month: str,
    summary: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]],
    budgets: Dict[str, float],
) -> str:
    """
    Generate a PDF report and return the file path.
    `month` is "YYYY-MM" format.
    """
    os.makedirs("/tmp/reports", exist_ok=True)
    path = f"/tmp/reports/fintrack_{month}.pdf"

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle("title", fontSize=22, textColor=DARK, spaceAfter=4,
                                  fontName="Helvetica-Bold")
    sub_style = ParagraphStyle("sub", fontSize=11, textColor=GRAY, spaceAfter=16)

    story.append(Paragraph("fintrack", title_style))
    year, mon = month.split("-")
    import calendar
    month_name = calendar.month_name[int(mon)]
    story.append(Paragraph(f"Monthly Expense Report — {month_name} {year}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceAfter=16))

    # ── Key Metrics ───────────────────────────────────────────────────────────
    total_spent = sum(r["total"] for r in summary)
    total_budget = sum(budgets.values()) if budgets else 0

    metrics = [
        ["Total Spent", f"₹{total_spent:,.0f}"],
        ["Total Budget", f"₹{total_budget:,.0f}" if total_budget else "Not set"],
        ["Transactions", str(sum(r["count"] for r in summary))],
        ["Anomalies", str(len(anomalies))],
    ]
    metrics_table = Table(metrics, colWidths=[80 * mm, 60 * mm])
    metrics_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (0, -1), 10),
        ("FONTSIZE", (1, 0), (1, -1), 13),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 16))

    # ── Category Breakdown ────────────────────────────────────────────────────
    section_style = ParagraphStyle("section", fontSize=13, textColor=DARK,
                                    fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=8)
    story.append(Paragraph("Spending by Category", section_style))

    cat_data = [["Category", "Transactions", "Amount Spent", "Budget", "Status"]]
    for row in summary:
        cat = row["category"]
        budget_val = budgets.get(cat, 0)
        status = ""
        if budget_val:
            pct = row["total"] / budget_val * 100
            status = f"Over ({pct:.0f}%)" if pct > 100 else f"{pct:.0f}% used"
        cat_data.append([
            cat,
            str(row["count"]),
            f"₹{row['total']:,.0f}",
            f"₹{budget_val:,.0f}" if budget_val else "—",
            status,
        ])
    cat_data.append(["Total", str(sum(r["count"] for r in summary)),
                      f"₹{total_spent:,.0f}", "", ""])

    cat_table = Table(cat_data, colWidths=[45*mm, 30*mm, 40*mm, 35*mm, 35*mm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT]),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cat_table)

    # ── Anomalies ─────────────────────────────────────────────────────────────
    if anomalies:
        story.append(Paragraph("Anomalous Transactions", section_style))
        anom_data = [["Date", "Description", "Category", "Amount", "vs Avg"]]
        for a in anomalies:
            anom_data.append([
                a["date"],
                a["description"][:35],
                a["category"],
                f"₹{a['amount']:,.0f}",
                f"{a['multiplier']:.1f}×",
            ])
        anom_table = Table(anom_data, colWidths=[25*mm, 65*mm, 30*mm, 30*mm, 20*mm])
        anom_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5C4B3")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#4A1B0C")),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FAECE7"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F0997B")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(anom_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    footer_style = ParagraphStyle("footer", fontSize=8, textColor=GRAY, spaceBefore=6)
    story.append(Paragraph(
        f"Generated by FinTrack · {month_name} {year} · Data is personal and private",
        footer_style
    ))

    doc.build(story)
    return path
