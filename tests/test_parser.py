import textwrap

from RenderStudy import markdown_parser, yaml_parser
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


def test_parse_yaml_structure():
    yaml_text = textwrap.dedent(
        """
        title: "1 Введение"
        subtitle: "1.1 Цель"
        context: "Тестовый абзац."
        ordered_list:
          - Первый
          - Второй
        bullet_list:
          - Пункт A
          - Пункт B
        image:
          path: "diagram.png"
          caption: "Схема"
        formula:
          expression: "E = mc^2"
          terms:
            - "E — энергия"
            - "m — масса"
            - "c — скорость света"
        """
    )
    document = yaml_parser.parse_yaml_document(yaml_text)
    assert isinstance(document.blocks[0], Heading)
    assert isinstance(document.blocks[1], Heading)
    assert isinstance(document.blocks[2], Paragraph)
    assert isinstance(document.blocks[3], ListBlock) and document.blocks[3].ordered
    assert isinstance(document.blocks[4], ListBlock) and not document.blocks[4].ordered
    assert isinstance(document.blocks[5], ImageBlock)
    assert isinstance(document.blocks[6], EquationBlock)
    assert document.blocks[6].terms and len(document.blocks[6].terms) == 3
