from RenderStudy import markdown_parser
from RenderStudy.model import (
    EquationBlock,
    Heading,
    ImageBlock,
    InlineEquation,
    ListBlock,
    Paragraph,
)


def test_parse_blocks_and_inline():
    md_text = """
# 1 Введение

Текст с *курсивом*, **жирным** и встроенной формулой $E=mc^2$.

- Первый пункт
- Второй пункт

![Схема](diagram.png "Схема процесса")

$$
S = \\pi r^2
$$
"""
    document = markdown_parser.parse_markdown(md_text)
    assert isinstance(document.blocks[0], Heading)
    assert isinstance(document.blocks[1], Paragraph)
    assert any(isinstance(item, InlineEquation) for item in document.blocks[1].inline)
    assert isinstance(document.blocks[2], ListBlock)
    assert isinstance(document.blocks[3], ImageBlock)
    assert isinstance(document.blocks[4], EquationBlock)
