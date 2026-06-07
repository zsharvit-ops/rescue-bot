"""
Generates a PDF search & rescue report using HTML + weasyprint.
RTL Hebrew is fully supported via CSS direction: rtl.
"""

import os
from datetime import datetime

from extractor import FIELDS


COLORS = {
    "header_bg": "#1A5376",
    "header_text": "#FFFFFF",
    "row_even": "#D6EAF8",
    "row_odd": "#FFFFFF",
    "summary_label": "#1A5376",
    "summary_value": "#EBF5FB",
    "title_color": "#1A5376",
}


def _html_escape(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_html(fields: dict, transcript: str, summary: dict = None) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── Summary section ──────────────────────────────────────────────────────
    summary_rows = ""
    if summary:
        summary_items = [
            ("תיאור המקרה", summary.get("case_summary", "")),
            ("מיקום אחרון ידוע", summary.get("last_location", "")),
            ("מצב רפואי", summary.get("medical_status", "")),
            ("זמן מאז נעדר", summary.get("time_missing", "")),
            ("תיאור אישי", summary.get("physical_description", "")),
        ]
        for label, value in summary_items:
            if value:
                summary_rows += f"""
                <tr>
                  <td class="sum-val">{_html_escape(value)}</td>
                  <td class="sum-label">{_html_escape(label)}</td>
                </tr>"""

    # ── Fields table ─────────────────────────────────────────────────────────
    field_rows = ""
    for i, (heb_label, key) in enumerate(FIELDS):
        value = fields.get(key) or ""
        bg = COLORS["row_even"] if i % 2 == 0 else COLORS["row_odd"]
        field_rows += f"""
        <tr style="background:{bg}">
          <td class="val-cell">{_html_escape(str(value))}</td>
          <td class="label-cell">{_html_escape(heb_label)}</td>
        </tr>"""

    # ── Transcript ───────────────────────────────────────────────────────────
    transcript_html = ""
    for line in (transcript or "").splitlines():
        line = line.strip()
        if not line:
            transcript_html += "<br>"
            continue
        if ":" in line:
            speaker, _, rest = line.partition(":")
            transcript_html += (
                f'<p class="transcript-line">'
                f'<span class="speaker">{_html_escape(speaker)}:</span> '
                f'{_html_escape(rest.strip())}</p>'
            )
        else:
            transcript_html += f'<p class="transcript-line">{_html_escape(line)}</p>'

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Heebo', 'Arial', 'Noto Sans Hebrew', sans-serif;
    direction: rtl;
    font-size: 11pt;
    color: #222;
    padding: 20mm 15mm;
  }}

  h1.doc-title {{
    color: {COLORS['title_color']};
    font-size: 22pt;
    text-align: center;
    margin-bottom: 4pt;
  }}

  .doc-date {{
    text-align: center;
    color: #666;
    margin-bottom: 16pt;
    font-size: 10pt;
  }}

  h2.section-title {{
    background: {COLORS['header_bg']};
    color: white;
    padding: 6pt 10pt;
    font-size: 13pt;
    margin: 14pt 0 6pt 0;
    border-radius: 3pt;
  }}

  /* Summary table */
  table.summary {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10pt;
  }}
  td.sum-label {{
    background: {COLORS['summary_label']};
    color: white;
    font-weight: bold;
    width: 30%;
    padding: 6pt 8pt;
    border: 1px solid #ccc;
    text-align: right;
  }}
  td.sum-val {{
    background: {COLORS['summary_value']};
    width: 70%;
    padding: 6pt 8pt;
    border: 1px solid #ccc;
    text-align: right;
  }}

  /* Fields table */
  table.fields {{
    width: 100%;
    border-collapse: collapse;
  }}
  th.fields-header {{
    background: {COLORS['header_bg']};
    color: white;
    padding: 7pt 8pt;
    text-align: right;
    border: 1px solid #aaa;
    font-size: 11pt;
  }}
  td.label-cell {{
    width: 35%;
    padding: 5pt 8pt;
    border: 1px solid #ddd;
    text-align: right;
    font-weight: bold;
    color: #1A5376;
  }}
  td.val-cell {{
    width: 65%;
    padding: 5pt 8pt;
    border: 1px solid #ddd;
    text-align: right;
  }}

  /* Transcript */
  .transcript-box {{
    background: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 3pt;
    padding: 10pt 12pt;
    margin-top: 6pt;
  }}
  p.transcript-line {{
    margin: 4pt 0;
    line-height: 1.6;
    text-align: right;
  }}
  span.speaker {{
    font-weight: bold;
    color: {COLORS['header_bg']};
  }}

  /* Page break */
  .page-break {{ page-break-before: always; }}
</style>
</head>
<body>

<h1 class="doc-title">דוח תחקיר חילוץ והצלה</h1>
<p class="doc-date">תאריך הפקה: {now}</p>

{"<h2 class='section-title'>סיכום מצב — מידע קריטי</h2>" if summary_rows else ""}
{"<table class='summary'>" + summary_rows + "</table>" if summary_rows else ""}

<h2 class="section-title">חלק א׳ — פרטי מחולץ ומקרה</h2>
<table class="fields">
  <tr>
    <th class="fields-header" style="width:65%">ערך</th>
    <th class="fields-header" style="width:35%">שדה</th>
  </tr>
  {field_rows}
</table>

<div class="page-break"></div>

<h2 class="section-title">חלק ב׳ — תמלול השיחה המלא</h2>
<div class="transcript-box">
  {transcript_html}
</div>

</body>
</html>"""
    return html


def generate_pdf(fields: dict, transcript: str, summary: dict = None) -> str:
    """Generate an HTML report and return the file path."""
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join("output", f"rescue_report_{timestamp}.html")

    html_content = _build_html(fields, transcript, summary)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_path
