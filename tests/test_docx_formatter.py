from pathlib import Path

from docx import Document as DocxDocument
from docx.shared import Pt

from RenderStudy.docx_formatter import reformat_docx


def test_reformat_docx_applies_font_and_spacing(tmp_path: Path):
    src = tmp_path / "input.docx"
    out = tmp_path / "output.docx"

    doc = DocxDocument()
    p1 = doc.add_paragraph("ВВЕДЕНИЕ")
    p1.runs[0].font.name = "Calibri"
    p1.runs[0].font.size = Pt(11)
    p2 = doc.add_paragraph("Обычный абзац текста.")
    p2.runs[0].font.name = "Calibri"
    p2.runs[0].font.size = Pt(11)
    doc.save(src)

    reformat_docx(src, out)

    formatted = DocxDocument(out)
    heading = formatted.paragraphs[0]
    body = formatted.paragraphs[1]

    assert heading.runs[0].font.name == "Times New Roman"
    assert heading.runs[0].font.size.pt == 14.0
    assert body.runs[0].font.name == "Times New Roman"
    assert body.runs[0].font.size.pt == 14.0
    assert heading.paragraph_format.line_spacing == 1.0
    assert body.paragraph_format.line_spacing == 1.0

