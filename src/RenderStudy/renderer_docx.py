from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from . import gost_format
from .model import (
    Block,
    CodeBlock,
    Document,
    EquationBlock,
    Heading,
    HorizontalRule,
    ImageBlock,
    InlineEquation,
    InlineElement,
    InlineLink,
    InlineText,
    ListBlock,
    ListItem,
    PageBreak,
    Paragraph,
    TableBlock,
)


@dataclass
class RenderState:
    heading_counters: list[int] = field(default_factory=list)
    current_section: int = 0
    equation_counters: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    figure_counters: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    table_counters: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    asset_root: Path | None = None


LATEX_TO_UNICODE = {
    r"\pi": "π",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\sigma": "σ",
    r"\phi": "φ",
    r"\omega": "ω",
}


def render_document(doc: Document, output_path: str | Path, asset_root: Path | None = None) -> None:
    output_path = Path(output_path)
    state = RenderState(asset_root=asset_root)
    docx = DocxDocument()
    gost_format.apply_page_layout(docx)

    for block in doc.blocks:
        _dispatch_block(docx, block, state)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    docx.save(output_path)


def _dispatch_block(docx: DocxDocument, block: Block, state: RenderState) -> None:
    if isinstance(block, Heading):
        _render_heading(docx, block, state)
    elif isinstance(block, Paragraph):
        _render_paragraph(docx, block.inline)
    elif isinstance(block, ListBlock):
        _render_list(docx, block, state)
    elif isinstance(block, CodeBlock):
        _render_code_block(docx, block)
    elif isinstance(block, EquationBlock):
        _render_equation_block(docx, block, state)
    elif isinstance(block, ImageBlock):
        _render_image_block(docx, block, state)
    elif isinstance(block, HorizontalRule):
        _render_horizontal_rule(docx)
    elif isinstance(block, TableBlock):
        _render_table_block(docx, block, state)
    elif isinstance(block, PageBreak):
        docx.add_page_break()


def _render_heading(docx: DocxDocument, heading: Heading, state: RenderState) -> None:
    number = _compute_heading_number(heading, state)
    text = f"{number} {heading.text}" if heading.numbered and number else heading.text
    paragraph = docx.add_paragraph(text)
    centered = not heading.numbered
    for run in paragraph.runs:
        run.bold = True
    gost_format.apply_heading_format(paragraph, centered=centered)

    # Ensure blank line after heading
    spacer = docx.add_paragraph("")
    gost_format.apply_body_paragraph_format(spacer)


def _compute_heading_number(heading: Heading, state: RenderState) -> str | None:
    if not heading.numbered:
        return heading.raw_number

    if heading.raw_number:
        try:
            top = int(heading.raw_number.split(".")[0])
            state.current_section = top
        except ValueError:
            pass
        return heading.raw_number

    level = max(1, heading.level)
    while len(state.heading_counters) < level:
        state.heading_counters.append(0)
    state.heading_counters[level - 1] += 1
    for idx in range(level, len(state.heading_counters)):
        state.heading_counters[idx] = 0
    if level == 1:
        state.current_section = state.heading_counters[0]
    number_parts = [str(n) for n in state.heading_counters[:level] if n > 0]
    return ".".join(number_parts)


def _render_paragraph(docx: DocxDocument, inline_elements: Iterable[InlineElement]) -> None:
    paragraph = docx.add_paragraph()
    for inline in inline_elements:
        if isinstance(inline, InlineText):
            run = paragraph.add_run(inline.text)
            gost_format.set_run_font(run, bold=inline.bold, italic=inline.italic, code=inline.code)
        elif isinstance(inline, InlineLink):
            run = paragraph.add_run(inline.text)
            run.font.underline = True
            gost_format.set_run_font(run)
        elif isinstance(inline, InlineEquation):
            run = paragraph.add_run(_latex_to_plain_text(inline.latex))
            gost_format.set_run_font(run)
    gost_format.apply_body_paragraph_format(paragraph)


def _render_list(docx: DocxDocument, block: ListBlock, state: RenderState) -> None:
    style = "List Number" if block.ordered else "List Bullet"
    for item in block.items:
        paragraph = docx.add_paragraph(style=style)
        # Render first block of list item inline in this paragraph when possible
        if item.blocks and isinstance(item.blocks[0], Paragraph):
            for inline in item.blocks[0].inline:
                if isinstance(inline, InlineText):
                    run = paragraph.add_run(inline.text)
                    gost_format.set_run_font(run, bold=inline.bold, italic=inline.italic, code=inline.code)
                elif isinstance(inline, InlineEquation):
                    run = paragraph.add_run(inline.latex)
                    gost_format.set_run_font(run)
                elif isinstance(inline, InlineLink):
                    run = paragraph.add_run(inline.text)
                    run.font.underline = True
                    gost_format.set_run_font(run)
            remaining_blocks = item.blocks[1:]
        else:
            remaining_blocks = item.blocks
        gost_format.apply_body_paragraph_format(paragraph)
        for sub_block in remaining_blocks:
            _dispatch_block(docx, sub_block, state)


def _render_code_block(docx: DocxDocument, block: CodeBlock) -> None:
    paragraph = docx.add_paragraph()
    run = paragraph.add_run(block.code)
    gost_format.set_run_font(run, code=True)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = Pt(gost_format.LINE_SPACING_PT)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(gost_format.LINE_SPACING_PT)
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT


def _render_equation_block(docx: DocxDocument, block: EquationBlock, state: RenderState) -> None:
    # Blank line before
    spacer = docx.add_paragraph("")
    gost_format.apply_body_paragraph_format(spacer)
    spacer.paragraph_format.first_line_indent = Cm(0)

    section = state.current_section or 1
    state.equation_counters[section] += 1
    number = block.number or f"{section}.{state.equation_counters[section]}"

    # Paragraph with center alignment and right tab for number
    right_edge = docx.sections[0].page_width - docx.sections[0].right_margin
    right_pos = int(right_edge / 635)  # convert EMU to twips
    paragraph = docx.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = Pt(gost_format.LINE_SPACING_PT)
    paragraph.paragraph_format.tab_stops.add_tab_stop(right_pos, WD_TAB_ALIGNMENT.RIGHT)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    _append_math(paragraph, _latex_to_plain_text(block.latex))
    paragraph.add_run("\t")
    run_number = paragraph.add_run(f"({number})")
    gost_format.set_run_font(run_number)

    # Optional description of symbols as bullet list
    if block.terms:
        for term in block.terms:
            desc = docx.add_paragraph(style="List Bullet")
            run_desc = desc.add_run(term)
            gost_format.set_run_font(run_desc)
            desc.paragraph_format.first_line_indent = Cm(0)
            desc.paragraph_format.line_spacing = Pt(gost_format.LINE_SPACING_PT)
    # Blank line after
    spacer_after = docx.add_paragraph("")
    gost_format.apply_body_paragraph_format(spacer_after)
    spacer_after.paragraph_format.first_line_indent = Cm(0)


def _render_horizontal_rule(docx: DocxDocument) -> None:
    paragraph = docx.add_paragraph()
    run = paragraph.add_run("-" * 20)
    gost_format.set_run_font(run)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = Pt(gost_format.LINE_SPACING_PT)


def _render_image_block(docx: DocxDocument, block: ImageBlock, state: RenderState) -> None:
    spacer_before = docx.add_paragraph("")
    gost_format.apply_body_paragraph_format(spacer_before)
    spacer_before.paragraph_format.first_line_indent = Cm(0)

    image_path = Path(block.src)
    if state.asset_root:
        candidate = state.asset_root / block.src
        if candidate.exists():
            image_path = candidate

    paragraph = docx.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    try:
        run.add_picture(str(image_path))
    except FileNotFoundError:
        run.add_text(f"[Missing image: {image_path}]")
    gost_format.set_run_font(run)

    section = state.current_section or 1
    state.figure_counters[section] += 1
    caption_number = f"{section}.{state.figure_counters[section]}"
    caption_text = block.caption or (block.alt or "").strip() or "Описание рисунка"
    caption_paragraph = docx.add_paragraph(f"Рисунок {caption_number} – {caption_text}")
    gost_format.apply_caption_format(caption_paragraph)

    spacer_after = docx.add_paragraph("")
    gost_format.apply_body_paragraph_format(spacer_after)
    spacer_after.paragraph_format.first_line_indent = Cm(0)


def _render_table_block(docx: DocxDocument, block: TableBlock, state: RenderState) -> None:
    section = state.current_section or 1
    state.table_counters[section] += 1
    caption_number = f"{section}.{state.table_counters[section]}"
    caption_text = block.caption or "Название таблицы"
    title = docx.add_paragraph(f"Таблица {caption_number} – {caption_text}")
    gost_format.apply_caption_format(title)

    row_count = len(block.rows)
    col_count = len(block.header) if len(block.header) > 0 else (len(block.rows[0]) if block.rows else 1)
    table = docx.add_table(rows=1 + row_count, cols=col_count)
    table.style = "Table Grid"
    if block.header:
        for idx, cell_text in enumerate(block.header):
            cell = table.cell(0, idx)
            cell.text = cell_text
    for r_idx, row in enumerate(block.rows, start=1):
        for c_idx, cell_text in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = cell_text
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.first_line_indent = Cm(0)
                paragraph.paragraph_format.line_spacing = Pt(gost_format.LINE_SPACING_PT)
        for run in paragraph.runs:
            gost_format.set_run_font(run)

    spacer_after = docx.add_paragraph("")
    gost_format.apply_body_paragraph_format(spacer_after)
    spacer_after.paragraph_format.first_line_indent = Cm(0)


def _latex_to_plain_text(expr: str) -> str:
    """Convert a small subset of LaTeX commands to Unicode glyphs for DOCX text."""
    text = expr.strip()
    for latex, uni in LATEX_TO_UNICODE.items():
        text = text.replace(latex, uni)
    return text


def _append_math(paragraph, text: str) -> None:
    """Insert a simple Word math object centered in the paragraph."""
    omath_para = OxmlElement("m:oMathPara")
    omath_para_pr = OxmlElement("m:oMathParaPr")
    jc = OxmlElement("m:jc")
    jc.set(qn("m:val"), "center")
    omath_para_pr.append(jc)
    omath_para.append(omath_para_pr)
    oMath = OxmlElement("m:oMath")

    run = OxmlElement("m:r")
    text_el = OxmlElement("m:t")
    text_el.text = text
    run.append(text_el)
    oMath.append(run)
    omath_para.append(oMath)
    paragraph._p.append(omath_para)
