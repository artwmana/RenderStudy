from __future__ import annotations

import re
from pathlib import Path

from docx import Document as DocxDocument
from docx.shared import Cm

from . import gost_format

NON_NUMBERED_TITLES = {
    "СОДЕРЖАНИЕ",
    "РЕФЕРАТ",
    "ВВЕДЕНИЕ",
    "ЗАКЛЮЧЕНИЕ",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
    "ПРИЛОЖЕНИЯ",
}


def reformat_docx(input_path: str | Path, output_path: str | Path) -> None:
    """Normalize an existing DOCX to project GOST formatting."""
    src = Path(input_path)
    out = Path(output_path)
    doc = DocxDocument(str(src))
    gost_format.apply_page_layout(doc)

    for paragraph in doc.paragraphs:
        _format_paragraph(paragraph)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _format_table_paragraph(paragraph)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))


def _format_paragraph(paragraph) -> None:
    text = paragraph.text.strip()
    is_blank = text == ""
    is_non_numbered_heading = text.upper() in NON_NUMBERED_TITLES and text != ""
    is_numbered_heading = _looks_like_numbered_heading(text)

    if is_non_numbered_heading:
        gost_format.apply_heading_format(paragraph, centered=True, with_indent=False)
    elif is_numbered_heading:
        gost_format.apply_heading_format(paragraph, centered=False, with_indent=True)
    else:
        gost_format.apply_body_paragraph_format(paragraph)
        if is_blank:
            paragraph.paragraph_format.first_line_indent = Cm(0)

    if is_blank and not paragraph.runs:
        run = paragraph.add_run(" ")
        gost_format.set_run_font(run)
    else:
        for run in paragraph.runs:
            gost_format.set_run_font(run, bold=bool(run.bold), italic=bool(run.italic))


def _format_table_paragraph(paragraph) -> None:
    gost_format.apply_body_paragraph_format(paragraph)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    if not paragraph.runs:
        run = paragraph.add_run(" ")
        gost_format.set_run_font(run)
    else:
        for run in paragraph.runs:
            gost_format.set_run_font(run, bold=bool(run.bold), italic=bool(run.italic))


def _looks_like_numbered_heading(text: str) -> bool:
    if not text:
        return False
    return re.match(r"^\d+(?:\.\d+)*\s+\S", text) is not None

