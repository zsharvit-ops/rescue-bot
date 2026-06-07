"""
Generates a .docx search & rescue report with:
  Part 1 — structured table of extracted fields
  Part 2 — full original transcript
"""

import os
import tempfile
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from extractor import FIELDS  # reuse the ordered field definitions


def _set_rtl(paragraph):
    """Set paragraph direction to RTL."""
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    pPr.append(bidi)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def _set_cell_bg(cell, hex_color: str):
    """Set table cell background color."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_doc_rtl(doc: Document):
    """Set document-level RTL for all default paragraph styles."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    # Set body bidi
    sectPr = doc.sections[0]._sectPr
    bidi = OxmlElement("w:bidi")
    # Set default paragraph style to RTL
    styles = doc.styles
    for style in styles:
        try:
            pPr = style.element.get_or_add_pPr()
            b = OxmlElement("w:bidi")
            pPr.append(b)
            jc = OxmlElement("w:jc")
            jc.set(qn("w:val"), "right")
            pPr.append(jc)
        except Exception:
            pass


def _add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_heading(text, level=level)
    _set_rtl(p)
    return p


def generate_doc(fields: dict, transcript: str, summary: dict = None) -> str:
    """
    Build and save the Word document.
    Returns the path to the saved .docx file.
    """
    doc = Document()

    # ── Document-level RTL ──────────────────────────────────────────────────
    doc.sections[0].page_width = Cm(21)
    doc.sections[0].page_height = Cm(29.7)
    _set_doc_rtl(doc)

    # ── Title ───────────────────────────────────────────────────────────────
    title = doc.add_paragraph()
    _set_rtl(title)
    run = title.add_run("דוח תחקיר חילוץ והצלה")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x1A, 0x53, 0x76)

    date_p = doc.add_paragraph()
    _set_rtl(date_p)
    date_p.add_run(f"תאריך הפקה: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    doc.add_paragraph()

    # ════════════════════════════════════════════════════════════════════════
    # SUMMARY — quick situation overview
    # ════════════════════════════════════════════════════════════════════════
    if summary:
        _add_heading(doc, "סיכום מצב — מידע קריטי", level=1)

        sum_table = doc.add_table(rows=0, cols=2)
        sum_table.style = "Table Grid"
        sum_table.alignment = WD_TABLE_ALIGNMENT.RIGHT

        summary_fields = [
            ("תיאור המקרה", summary.get("case_summary", "")),
            ("מיקום אחרון ידוע", summary.get("last_location", "")),
            ("מצב רפואי", summary.get("medical_status", "")),
            ("זמן מאז נעדר", summary.get("time_missing", "")),
            ("תיאור אישי", summary.get("physical_description", "")),
        ]
        for label, value in summary_fields:
            if value:
                row_cells = sum_table.add_row().cells
                row_cells[0].text = label
                row_cells[1].text = str(value)
                _set_cell_bg(row_cells[0], "1A5376")
                for p in row_cells[0].paragraphs:
                    _set_rtl(p)
                    for r in p.runs:
                        r.bold = True
                        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        r.font.size = Pt(11)
                _set_cell_bg(row_cells[1], "EBF5FB")
                for p in row_cells[1].paragraphs:
                    _set_rtl(p)
                    for r in p.runs:
                        r.font.size = Pt(11)

        for row in sum_table.rows:
            row.cells[0].width = Cm(5)
            row.cells[1].width = Cm(12)

        doc.add_paragraph()

    # ════════════════════════════════════════════════════════════════════════
    # PART 1 — Extracted fields table
    # ════════════════════════════════════════════════════════════════════════
    _add_heading(doc, "חלק א׳ — פרטי מחולץ ומקרה", level=1)

    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.RIGHT

    # Header row
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "שדה"
    hdr_cells[1].text = "ערך"
    for cell in hdr_cells:
        _set_cell_bg(cell, "1A5376")
        for paragraph in cell.paragraphs:
            _set_rtl(paragraph)
            for run in paragraph.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(11)

    # Data rows
    for idx, (hebrew_label, key) in enumerate(FIELDS):
        value = fields.get(key) or ""
        if value is None:
            value = ""
        row_cells = table.add_row().cells
        row_cells[0].text = hebrew_label
        row_cells[1].text = str(value)

        bg = "D6EAF8" if idx % 2 == 0 else "FFFFFF"
        for cell in row_cells:
            _set_cell_bg(cell, bg)
            for paragraph in cell.paragraphs:
                _set_rtl(paragraph)
                for run in paragraph.runs:
                    run.font.size = Pt(10)

    # Column widths
    for row in table.rows:
        row.cells[0].width = Cm(6)
        row.cells[1].width = Cm(11)

    doc.add_page_break()

    # ════════════════════════════════════════════════════════════════════════
    # PART 2 — Full transcript
    # ════════════════════════════════════════════════════════════════════════
    _add_heading(doc, "חלק ב׳ — תמלול השיחה המלא", level=1)

    for line in transcript.splitlines():
        p = doc.add_paragraph(line or " ")
        _set_rtl(p)
        p.runs[0].font.size = Pt(10) if p.runs else None

    # ── Save ─────────────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", f"rescue_report_{timestamp}.docx")
    doc.save(out_path)
    return out_path
