from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from markdown_it import MarkdownIt
from mdit_py_plugins.texmath import texmath_plugin

from .model import (
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
    Paragraph,
    TableBlock,
)


@dataclass
class _InlineImage:
    src: str
    alt: str | None
    title: str | None


def parse_markdown(text: str) -> Document:
    md = MarkdownIt("commonmark").use(texmath_plugin).enable(["table"])
    tokens = md.parse(text)
    blocks, _ = _parse_blocks(tokens, 0, stop_types=set())
    return Document(blocks=blocks)


def _parse_blocks(tokens, index: int, stop_types: set[str]) -> tuple[list, int]:
    blocks: List = []
    i = index
    while i < len(tokens):
        tok = tokens[i]
        if tok.type in stop_types:
            break
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            inline = tokens[i + 1]
            text = inline.content.strip()
            clean_text, number, numbered = _extract_heading_parts(text)
            blocks.append(Heading(level=level, text=clean_text, numbered=numbered, raw_number=number))
            i += 3
        elif tok.type == "paragraph_open":
            inline = tokens[i + 1]
            mixed_equation = _extract_equation_from_paragraph(inline.content or "")
            if mixed_equation is not None:
                prefix_text, latex, terms, suffix_text = mixed_equation
                if prefix_text:
                    blocks.append(Paragraph(inline=[InlineText(prefix_text)]))
                blocks.append(EquationBlock(latex=latex, display=True, number=None, terms=terms or None))
                if suffix_text:
                    blocks.append(Paragraph(inline=[InlineText(suffix_text)]))
                i += 3
                continue
            display_latex = _extract_display_math_inline(inline.content or "")
            if display_latex is not None:
                terms = None
                consumed = 0
                if i + 3 < len(tokens):
                    terms, consumed = _collect_term_paragraphs(tokens, i + 3)
                blocks.append(EquationBlock(latex=display_latex, display=True, number=None, terms=terms))
                i += 3 + consumed
                continue
            inline_elements = _parse_inline(inline.children or [])
            if len(inline_elements) == 1 and isinstance(inline_elements[0], _InlineImage):
                image = inline_elements[0]
                blocks.append(ImageBlock(src=image.src, alt=image.alt, caption=image.title))
            else:
                blocks.append(Paragraph(inline=inline_elements))
            i += 3
        elif tok.type in ("bullet_list_open", "ordered_list_open"):
            ordered = tok.type == "ordered_list_open"
            i += 1
            items: list[ListItem] = []
            while i < len(tokens) and tokens[i].type != ("ordered_list_close" if ordered else "bullet_list_close"):
                if tokens[i].type == "list_item_open":
                    i += 1
                    item_blocks, i = _parse_blocks(tokens, i, stop_types={"list_item_close"})
                    items.append(ListItem(blocks=item_blocks))
                    i += 1  # skip list_item_close
                else:
                    i += 1
            blocks.append(ListBlock(items=items, ordered=ordered))
            i += 1  # skip list close
        elif tok.type == "fence":
            blocks.append(CodeBlock(language=tok.info or None, code=tok.content))
            i += 1
        elif tok.type == "math_block":
            latex = tok.content.strip()
            terms = None
            # Look ahead for one or more paragraphs with symbol explanations
            if i + 1 < len(tokens):
                terms, consumed = _collect_term_paragraphs(tokens, i + 1)
                if consumed:
                    i += consumed
            blocks.append(EquationBlock(latex=latex, display=True, number=None, terms=terms))
            i += 1
        elif tok.type == "hr":
            blocks.append(HorizontalRule())
            i += 1
        elif tok.type == "table_open":
            table_block, i = _parse_table(tokens, i)
            blocks.append(table_block)
        else:
            i += 1
    return blocks, i


def _parse_table(tokens, index: int) -> tuple[TableBlock, int]:
    header: list[str] = []
    rows: list[list[str]] = []
    i = index + 1
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "thead_open":
            i += 1
            # parse header row
            while tokens[i].type != "thead_close":
                if tokens[i].type == "th_open":
                    inline = tokens[i + 1]
                    header.append(_inline_text_from_children(inline.children or []))
                    i += 3  # skip th_open, inline, th_close
                else:
                    i += 1
            i += 1
        elif tok.type == "tbody_open":
            i += 1
            while tokens[i].type != "tbody_close":
                if tokens[i].type == "tr_open":
                    row: list[str] = []
                    i += 1
                    while tokens[i].type != "tr_close":
                        if tokens[i].type in {"td_open", "th_open"}:
                            inline = tokens[i + 1]
                            row.append(_inline_text_from_children(inline.children or []))
                            i += 3
                        else:
                            i += 1
                    rows.append(row)
                    i += 1  # skip tr_close
                else:
                    i += 1
            i += 1
        elif tok.type == "table_close":
            break
        else:
            i += 1
    return TableBlock(header=header, rows=rows), i + 1


def _parse_inline(children: Iterable) -> List[InlineElement | _InlineImage]:
    result: List[InlineElement | _InlineImage] = []
    bold = False
    italic = False
    i = 0
    children_list = list(children)
    while i < len(children_list):
        tok = children_list[i]
        if tok.type == "text":
            result.append(InlineText(tok.content, bold=bold, italic=italic))
            i += 1
        elif tok.type == "softbreak":
            result.append(InlineText(" ", bold=bold, italic=italic))
            i += 1
        elif tok.type == "strong_open":
            bold = True
            i += 1
        elif tok.type == "strong_close":
            bold = False
            i += 1
        elif tok.type == "em_open":
            italic = True
            i += 1
        elif tok.type == "em_close":
            italic = False
            i += 1
        elif tok.type == "code_inline":
            result.append(InlineText(tok.content, bold=bold, italic=italic, code=True))
            i += 1
        elif tok.type in {"math_inline", "math_single"}:
            result.append(InlineEquation(tok.content))
            i += 1
        elif tok.type == "link_open":
            href = tok.attrGet("href") or ""
            link_text, consumed = _collect_text(children_list, i + 1, "link_close")
            result.append(InlineLink(text=link_text or href, url=href))
            i = consumed + 1
        elif tok.type == "image":
            src = tok.attrGet("src") or ""
            alt = tok.content or tok.attrGet("alt")
            title = tok.attrGet("title")
            result.append(_InlineImage(src=src, alt=alt, title=title))
            i += 1
        else:
            i += 1
    return result


def _collect_text(tokens: Sequence, index: int, closing_type: str) -> tuple[str, int]:
    texts: list[str] = []
    i = index
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == closing_type:
            break
        if tok.type == "text":
            texts.append(tok.content)
        i += 1
    return "".join(texts), i


def _inline_text_from_children(children: Iterable) -> str:
    texts: list[str] = []
    for child in children:
        if child.type == "text":
            texts.append(child.content)
        elif child.type == "code_inline":
            texts.append(child.content)
    return "".join(texts)


def _inline_lines(children: Iterable) -> list[str]:
    lines: list[str] = [""]
    for child in children:
        if child.type == "text":
            lines[-1] += child.content
        elif child.type in {"math_inline", "math_single"}:
            lines[-1] += f"${child.content}$"
        elif child.type == "code_inline":
            lines[-1] += child.content
        elif child.type in {"softbreak", "hardbreak"}:
            lines.append("")
    return [line.strip() for line in lines if line.strip()]


def _looks_like_term(line: str) -> bool:
    return "-" in line or "—" in line or "–" in line


def _strip_where_prefix(line: str) -> str:
    stripped = line.strip()
    if stripped.lower() == "где" or stripped.lower() == "where":
        return ""
    if stripped.lower().startswith("где "):
        return stripped[4:].strip()
    if stripped.lower().startswith("where "):
        return stripped[6:].strip()
    return stripped


def _collect_term_paragraphs(tokens, index: int) -> tuple[list[str] | None, int]:
    terms: list[str] = []
    i = index
    consumed = 0
    saw_where = False
    while i + 2 < len(tokens) and tokens[i].type == "paragraph_open":
        inline = tokens[i + 1]
        if inline.type != "inline":
            break
        lines = _inline_lines(inline.children or [])
        if not lines:
            break
        line_is_terms = all(_looks_like_term(line) for line in lines)
        line_is_where = len(lines) == 1 and lines[0].strip().lower() in {"где", "where"}
        line_is_where_with_term = all(line.lower().startswith("где ") or line.lower().startswith("where ") for line in lines)
        if not (line_is_terms or line_is_where or line_is_where_with_term):
            break
        if line_is_where or line_is_where_with_term:
            saw_where = True
        for line in lines:
            stripped = _strip_where_prefix(line)
            if stripped:
                terms.append(stripped)
        i += 3
        consumed += 3
    if not terms and not saw_where:
        return None, 0
    return (terms if terms else None), consumed


def _extract_display_math_inline(text: str) -> str | None:
    stripped = text.strip()
    if not (stripped.startswith("$$") and stripped.endswith("$$")):
        return None
    inner = stripped[2:-2].strip()
    return inner or None


def _extract_equation_from_paragraph(text: str) -> tuple[str, str, list[str], str] | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    formula_idx = None
    formula_text = ""
    for idx, line in enumerate(lines):
        if "$$" in line:
            first = line.find("$$")
            second = line.find("$$", first + 2)
            if second != -1:
                formula_idx = idx
                formula_text = line[first + 2 : second].strip()
                break
    if formula_idx is None or not formula_text:
        return None

    prefix_text = " ".join(lines[:formula_idx]).strip()
    trailing_lines = lines[formula_idx + 1 :]
    terms: list[str] = []
    suffix_lines: list[str] = []
    for line in trailing_lines:
        lowered = line.lower()
        if lowered == "где" or lowered == "where":
            continue
        if lowered.startswith("где "):
            line = line[4:].strip()
        elif lowered.startswith("where "):
            line = line[6:].strip()
        if _looks_like_term(line):
            terms.append(line)
        else:
            suffix_lines.append(line)
    suffix_text = " ".join(suffix_lines).strip()
    return prefix_text, formula_text, terms, suffix_text


def _extract_heading_parts(text: str) -> tuple[str, str | None, bool]:
    match = re.match(r"(?P<num>(\d+(\.\d+)*))\s+(?P<title>.+)", text)
    if match:
        return match.group("title").strip(), match.group("num"), True
    return text, None, False
