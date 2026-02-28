from __future__ import annotations

from pathlib import Path

from . import docx_formatter, markdown_parser, renderer_docx, yaml_parser


def find_title_template(input_path: Path) -> Path | None:
    candidate = input_path.parent / "титульник.docx"
    if candidate.exists():
        return candidate
    return None


def convert_input_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    use_title_template: bool = True,
    title_template_path: Path | None = None,
    extracted_md_path: str | Path | None = None,
) -> None:
    src = Path(input_path)
    out = Path(output_path)
    suffix = src.suffix.lower()

    if suffix == ".docx":
        docx_formatter.rebuild_docx_via_markdown(
            input_path=src,
            output_path=out,
            extracted_md_path=extracted_md_path,
            title_template_path=title_template_path,
        )
        return

    text = src.read_text(encoding="utf-8")
    template_path = None
    if suffix == ".md":
        if title_template_path is not None:
            template_path = title_template_path
        elif use_title_template:
            template_path = find_title_template(src)

    if suffix in {".yaml", ".yml"}:
        document = yaml_parser.parse_yaml_document(text)
    else:
        document = markdown_parser.parse_markdown(text)

    renderer_docx.render_document(
        document,
        output_path=out,
        asset_root=src.parent,
        template_path=template_path,
    )


def convert_text_to_docx(text: str, output_path: str | Path, title_template_path: Path | None = None) -> None:
    out = Path(output_path)
    document = markdown_parser.parse_markdown(text)
    renderer_docx.render_document(
        document,
        output_path=out,
        asset_root=out.parent,
        template_path=title_template_path,
    )
