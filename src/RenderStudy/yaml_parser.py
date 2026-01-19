from __future__ import annotations

import re
from typing import Iterable, List

import yaml

from .model import (
    CodeBlock,
    Document,
    EquationBlock,
    Heading,
    ImageBlock,
    InlineText,
    ListBlock,
    ListItem,
    Paragraph,
    TableBlock,
)


def parse_yaml_document(text: str) -> Document:
    """Parse a constrained YAML structure into an internal Document AST."""
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping with defined fields.")

    blocks = []

    body = data.get("body")
    if isinstance(body, list):
        blocks.extend(_parse_body_sequence(body))
        return Document(blocks=blocks, metadata={"source": "yaml"})

    for key, value in data.items():
        if key in {"title", "heading"}:
            if value:
                blocks.append(_heading_from_text(value, level=1))
        elif key == "subtitle":
            if value:
                blocks.append(_heading_from_text(value, level=2))
        elif key in {"context", "extra_paragraph"}:
            if value:
                blocks.extend(_paragraphs_from_text(str(value)))
        elif key in {"ordered_list", "numbered_list"}:
            items = _normalize_list(value)
            if items:
                blocks.append(_list_block(items, ordered=True))
        elif key in {"bullet_list", "unordered_list"}:
            items = _normalize_list(value)
            if items:
                blocks.append(_list_block(items, ordered=False))
        elif key == "image":
            img_block = _build_image(value, data)
            if img_block:
                blocks.append(img_block)
        elif key == "formula":
            eq_block = _build_formula(value)
            if eq_block:
                blocks.append(eq_block)
        elif key == "table":
            tbl_block = _build_table(value)
            if tbl_block:
                blocks.append(tbl_block)
        elif key == "code_block":
            if value:
                blocks.append(CodeBlock(language=None, code=str(value)))

    return Document(blocks=blocks, metadata={"source": "yaml"})


def _heading_from_text(text: str, level: int) -> Heading:
    clean, number, numbered = _extract_heading_parts(str(text))
    return Heading(level=level, text=clean, numbered=numbered, raw_number=number)


def _list_block(items: Iterable[str], ordered: bool) -> ListBlock:
    list_items: List[ListItem] = []
    for item in items:
        paragraph = Paragraph(inline=[InlineText(str(item))])
        list_items.append(ListItem(blocks=[paragraph]))
    return ListBlock(items=list_items, ordered=ordered)


def _build_image(image_value, root_dict) -> ImageBlock | None:
    if image_value is None:
        return None
    if isinstance(image_value, dict):
        src = image_value.get("path") or image_value.get("src")
        caption = image_value.get("caption")
        alt = image_value.get("alt")
    else:
        src = str(image_value)
        caption = root_dict.get("image_caption")
        alt = root_dict.get("image_alt")
    if not src:
        return None
    return ImageBlock(src=src, alt=alt, caption=caption)


def _build_formula(formula_value) -> EquationBlock | None:
    if formula_value is None:
        return None
    if isinstance(formula_value, dict):
        expr = formula_value.get("expression") or formula_value.get("latex") or formula_value.get("value")
        terms = formula_value.get("terms")
        if expr:
            return EquationBlock(latex=str(expr), display=True, terms=_normalize_list(terms) if terms else None)
        return None
    return EquationBlock(latex=str(formula_value), display=True)


def _build_table(table_value) -> TableBlock | None:
    if not table_value or not isinstance(table_value, dict):
        return None
    header = table_value.get("header") or []
    rows = table_value.get("rows") or []
    caption = table_value.get("caption")
    return TableBlock(header=list(header), rows=list(rows), caption=caption)


def _paragraphs_from_text(text: str) -> list[Paragraph]:
    """Split text into paragraphs on blank lines while preserving leading spaces."""
    parts = [p for p in text.split("\n\n") if p.strip()]
    if not parts:
        return []
    return [Paragraph(inline=[InlineText(part)]) for part in parts]


def _parse_body_sequence(body: list) -> list[Block]:
    """Parse an ordered list of block descriptors."""
    blocks: list[Block] = []
    for entry in body:
        if isinstance(entry, str):
            blocks.append(Paragraph(inline=[InlineText(entry)]))
            continue
        if not isinstance(entry, dict):
            continue
        if "heading" in entry:
            blocks.append(_heading_from_text(entry["heading"], level=entry.get("level", 1)))
        elif "paragraph" in entry:
            blocks.extend(_paragraphs_from_text(str(entry["paragraph"])))
        elif "ordered_list" in entry:
            blocks.append(_list_block(_normalize_list(entry["ordered_list"]), ordered=True))
        elif "bullet_list" in entry:
            blocks.append(_list_block(_normalize_list(entry["bullet_list"]), ordered=False))
        elif "image" in entry:
            img = _build_image(entry["image"], entry if isinstance(entry["image"], dict) else {})
            if img:
                blocks.append(img)
        elif "formula" in entry:
            eq = _build_formula(entry["formula"])
            if eq:
                blocks.append(eq)
        elif "table" in entry:
            tbl = _build_table(entry["table"])
            if tbl:
                blocks.append(tbl)
        elif "code_block" in entry:
            blocks.append(CodeBlock(language=None, code=str(entry["code_block"])))
    return blocks


def _normalize_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def _extract_heading_parts(text: str) -> tuple[str, str | None, bool]:
    match = re.match(r"(?P<num>(\d+(\.\d+)*))\s+(?P<title>.+)", text)
    if match:
        return match.group("title").strip(), match.group("num"), True
    return text, None, False
