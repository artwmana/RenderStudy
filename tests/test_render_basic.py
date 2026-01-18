from pathlib import Path

from RenderStudy.model import Document, EquationBlock, Heading, InlineText, Paragraph
from RenderStudy.renderer_docx import render_document


def test_render_creates_docx(tmp_path: Path):
    doc = Document(
        blocks=[
            Heading(level=1, text="Введение", numbered=True, raw_number="1"),
            Paragraph(inline=[InlineText("Пример абзаца для теста.")]),
            EquationBlock(latex="E = mc^2", display=True),
        ]
    )
    output_file = tmp_path / "report.docx"
    render_document(doc, output_file)
    assert output_file.exists()
    assert output_file.stat().st_size > 0
