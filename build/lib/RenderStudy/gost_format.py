from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297

FONT_NAME = "Times New Roman"
FONT_SIZE_PT = 14
LINE_SPACING_PT = 18
FIRST_LINE_INDENT_CM = 1.25

MARGIN_LEFT_CM = 3.0
MARGIN_RIGHT_CM = 1.5
MARGIN_TOP_CM = 2.0
MARGIN_BOTTOM_CM = 2.0


def apply_page_layout(doc) -> None:
    """Apply A4 page setup and required margins."""
    section = doc.sections[0]
    section.page_height = Cm(A4_HEIGHT_MM / 10)
    section.page_width = Cm(A4_WIDTH_MM / 10)
    section.left_margin = Cm(MARGIN_LEFT_CM)
    section.right_margin = Cm(MARGIN_RIGHT_CM)
    section.top_margin = Cm(MARGIN_TOP_CM)
    section.bottom_margin = Cm(MARGIN_BOTTOM_CM)


def _set_run_font(run, bold: bool = False, italic: bool = False, code: bool = False) -> None:
    run.font.name = FONT_NAME if not code else "Courier New"
    run.font.size = Pt(FONT_SIZE_PT)
    run.bold = bold
    run.italic = italic


def apply_body_paragraph_format(paragraph) -> None:
    """Format normal text according to BSUIR body text rules."""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
    paragraph.paragraph_format.first_line_indent = Cm(FIRST_LINE_INDENT_CM)


def apply_heading_format(paragraph, centered: bool = False) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(LINE_SPACING_PT)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    for run in paragraph.runs:
        _set_run_font(run, bold=True)


def apply_caption_format(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(LINE_SPACING_PT)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    for run in paragraph.runs:
        _set_run_font(run, bold=False)


def set_run_font(run, bold: bool = False, italic: bool = False, code: bool = False) -> None:
    """Public helper for inline rendering."""
    _set_run_font(run, bold=bold, italic=italic, code=code)
