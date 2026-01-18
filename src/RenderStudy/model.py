from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence


@dataclass
class Block:
    """Base class for block-level nodes."""


@dataclass
class Document:
    blocks: List[Block]
    metadata: dict[str, Any] | None = None


@dataclass
class Heading(Block):
    level: int
    text: str
    numbered: bool = True
    raw_number: str | None = None


@dataclass
class Paragraph(Block):
    inline: List["InlineElement"]


@dataclass
class ListItem:
    blocks: List[Block]


@dataclass
class ListBlock(Block):
    items: List[ListItem]
    ordered: bool


@dataclass
class CodeBlock(Block):
    language: str | None
    code: str


@dataclass
class ImageBlock(Block):
    src: str
    alt: str | None = None
    caption: str | None = None


@dataclass
class EquationBlock(Block):
    latex: str
    display: bool = True
    number: str | None = None


@dataclass
class HorizontalRule(Block):
    """Horizontal rule / thematic break."""


@dataclass
class TableBlock(Block):
    header: Sequence[str]
    rows: Sequence[Sequence[str]]
    caption: str | None = None


@dataclass
class PageBreak(Block):
    """Explicit page break marker."""


@dataclass
class InlineElement:
    """Base class for inline nodes."""


@dataclass
class InlineText(InlineElement):
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass
class InlineLink(InlineElement):
    text: str
    url: str


@dataclass
class InlineEquation(InlineElement):
    latex: str
