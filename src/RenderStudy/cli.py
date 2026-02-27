from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .conversion_service import convert_input_file
from .utils import configure_logging, resolve_output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="RenderStudy",
        description="Convert Markdown into DOCX formatted for BSUIR/STP 01-2024.",
    )
    parser.add_argument("input", type=str, help="Path to input file (.md/.yaml/.docx)")
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

    logging.info("Rendering DOCX to %s", output_path)
    convert_input_file(input_path=input_path, output_path=output_path, use_title_template=True)
    logging.info("Done. Saved to %s", output_path)


if __name__ == "__main__":
    main()
