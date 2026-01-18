from __future__ import annotations

import re
from typing import Iterable, List

import yaml

from .model import (
    Document,
    EquationBlock,
    Heading,
    ImageBlock,
    InlineText,
    ListBlock,
    ListItem,
    Paragraph,
)


def parse_yaml_document(text: str) -> Document:
    """Parse a constrained YAML structure into an internal Document AST."""
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping with defined fields.")

    blocks = []

    title = data.get("title") or data.get("heading")
    if title:
        blocks.append(_heading_from_text(title, level=1))

    subtitle = data.get("subtitle")
    if subtitle:
        blocks.append(_heading_from_text(subtitle, level=2))

    context = data.get("context")
    if context:
        blocks.append(Paragraph(inline=[InlineText(str(context))]))

    ordered_items = _normalize_list(data.get("ordered_list") or data.get("numbered_list"))
    if ordered_items:
        blocks.append(_list_block(ordered_items, ordered=True))

    bullet_items = _normalize_list(data.get("bullet_list") or data.get("unordered_list"))
    if bullet_items:
        blocks.append(_list_block(bullet_items, ordered=False))

    image = data.get("image")
    if image:
        if isinstance(image, dict):
            src = image.get("path") or image.get("src")
            caption = image.get("caption")
            alt = image.get("alt")
        else:
            src = str(image)
            caption = data.get("image_caption")
            alt = data.get("image_alt")
        if src:
            blocks.append(ImageBlock(src=src, alt=alt, caption=caption))

    formula = data.get("formula")
    if formula:
        if isinstance(formula, dict):
            expr = formula.get("expression") or formula.get("latex") or formula.get("value")
            terms = formula.get("terms")
            if expr:
                blocks.append(EquationBlock(latex=str(expr), display=True, terms=_normalize_list(terms) if terms else None))
        else:
            blocks.append(EquationBlock(latex=str(formula), display=True))

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
