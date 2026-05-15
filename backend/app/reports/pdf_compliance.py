from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _p(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_compliance_pdf(title: str, sections: dict[str, Any]) -> bytes:
    """Render a governance-style PDF from structured section payloads."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#16213e"),
    )
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=12)

    story: list[Any] = []
    story.append(Paragraph(_p(title), h1))
    org = sections.get("organization_name")
    if isinstance(org, str) and org:
        story.append(Paragraph(_p(f"Organization: {org}"), body))
    period = sections.get("period") or {}
    if isinstance(period, dict):
        ps, pe = period.get("start"), period.get("end")
        if ps and pe:
            story.append(Paragraph(_p(f"Reporting period: {ps} — {pe}"), body))
    story.append(Spacer(1, 0.15 * inch))

    def add_heading(text: str) -> None:
        story.append(Paragraph(_p(text), h2))

    def add_bullets(items: list[str]) -> None:
        for line in items[:40]:
            story.append(Paragraph(_p(f"• {line}"), body))

    usage = sections.get("ai_tool_usage_summary") or {}
    add_heading("1. AI tool usage summary")
    if isinstance(usage, dict) and usage.get("by_tool"):
        data = [["Tool", "Vendor", "Events"]] + [
            [str(r.get("tool", "")), str(r.get("vendor", "")), str(r.get("count", ""))]
            for r in usage["by_tool"][:20]
        ]
        t = Table(data, colWidths=[2.2 * inch, 2.2 * inch, 1.2 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8ef")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ],
            ),
        )
        story.append(t)
    else:
        story.append(Paragraph(_p("No AI-related detection events in period."), body))
    story.append(Spacer(1, 0.12 * inch))

    high = sections.get("high_risk_events") or []
    add_heading("2. High risk events")
    if isinstance(high, list) and high:
        rows = [["When", "Tool", "Severity", "Score"]]
        for e in high[:15]:
            rows.append(
                [
                    str(e.get("occurred_at", ""))[:19],
                    str(e.get("tool_name", ""))[:28],
                    str(e.get("severity", "")),
                    str(e.get("risk_score", "")),
                ],
            )
        t = Table(rows, colWidths=[1.35 * inch, 2.0 * inch, 0.9 * inch, 0.85 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffe0e0")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ],
            ),
        )
        story.append(t)
    else:
        story.append(Paragraph(_p("No high or critical severity events in period."), body))
    story.append(Spacer(1, 0.12 * inch))

    pii = sections.get("possible_pii_exposure") or []
    add_heading("3. Possible PII exposure")
    if isinstance(pii, list) and pii:
        for item in pii[:12]:
            line = f"{item.get('occurred_at', '')} — {item.get('tool_name', '')}: {item.get('summary', '')}"
            story.append(Paragraph(_p(line[:500]), body))
    else:
        story.append(Paragraph(_p("No PII keyword rule hits linked to AI events in period."), body))
    story.append(Spacer(1, 0.12 * inch))

    users = sections.get("top_users") or []
    add_heading("4. Top users (by detection count)")
    if isinstance(users, list) and users:
        data = [["User / principal", "Detections"]] + [
            [str(u.get("user", "Unknown"))[:48], str(u.get("count", ""))] for u in users[:15]
        ]
        t = Table(data, colWidths=[4.5 * inch, 1.1 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f4ea")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ],
            ),
        )
        story.append(t)
    else:
        story.append(Paragraph(_p("Insufficient user attribution in telemetry."), body))
    story.append(Spacer(1, 0.12 * inch))

    rs = sections.get("risk_score") or {}
    add_heading("5. Risk score overview")
    if isinstance(rs, dict):
        story.append(
            Paragraph(
                _p(
                    f"Average detection score: {rs.get('avg_detection_score', 'n/a')} · "
                    f"Events in period: {rs.get('event_count', 0)} · "
                    f"By severity: {rs.get('by_severity', {})}",
                ),
                body,
            ),
        )
    story.append(Spacer(1, 0.12 * inch))

    rec = sections.get("recommendations") or []
    add_heading("6. Recommendations")
    if isinstance(rec, list) and rec:
        add_bullets([str(x) for x in rec])
    else:
        story.append(Paragraph(_p("Continue monitoring and refine policies as detections grow."), body))
    story.append(Spacer(1, 0.12 * inch))

    adm = sections.get("adm_activity_summary") or {}
    add_heading("7. ADM-related activity summary")
    if isinstance(adm, dict):
        story.append(
            Paragraph(
                _p(
                    f"Sample window: {adm.get('source', 'Microsoft Graph directory audits')} · "
                    f"Matching events: {adm.get('match_count', 0)}",
                ),
                body,
            ),
        )
        samples = adm.get("sample_activities") or []
        if isinstance(samples, list):
            add_bullets([str(s)[:200] for s in samples[:10]])
    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            _p(
                "Generated by Scanlyr compliance reporting. "
                "Rule-based analysis; validate findings in Microsoft 365 / Entra admin centers.",
            ),
            ParagraphStyle("Foot", parent=body, fontSize=8, textColor=colors.grey),
        ),
    )

    doc.build(story)
    return buf.getvalue()
