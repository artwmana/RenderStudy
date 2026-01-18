from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import markdown_parser, renderer_docx
from .utils import configure_logging, read_markdown, resolve_output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="RenderStudy",
        description="Convert Markdown into DOCX formatted for BSUIR/STP 01-2024.",
    )
    parser.add_argument("input", type=str, help="Path to Markdown file")
    parser.add_argument("-o", "--output", type=str, help="Output DOCX path")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)
    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    output_path = resolve_output_path(input_path, args.output)

    logging.info("Reading %s", input_path)
    markdown_text = read_markdown(input_path)
    logging.debug("Markdown length: %d chars", len(markdown_text))

    logging.info("Parsing markdown...")
    document = markdown_parser.parse_markdown(markdown_text)

    logging.info("Rendering DOCX to %s", output_path)
    renderer_docx.render_document(document, output_path=output_path, asset_root=input_path.parent)

    logging.info("Done. Saved to %s", output_path)


if __name__ == "__main__":
    main()
