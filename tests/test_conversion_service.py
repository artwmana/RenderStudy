from pathlib import Path

from docx import Document as DocxDocument

from RenderStudy.conversion_service import convert_text_to_docx


def test_convert_text_to_docx(tmp_path: Path):
    out = tmp_path / "text.docx"
    convert_text_to_docx("# ВВЕДЕНИЕ\n\nТекст абзаца.", out)
    assert out.exists()
    assert out.stat().st_size > 0
    doc = DocxDocument(out)
    assert any("ВВЕДЕНИЕ" in p.text for p in doc.paragraphs)

