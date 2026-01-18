from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def configure_logging(verbose: bool = False) -> None:
    """Configure a simple console logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(message)s",
    )


def resolve_output_path(input_path: Path, output: Optional[str]) -> Path:
    if output:
        out_path = Path(output)
        if out_path.is_dir():
            out_path = out_path / f"{input_path.stem}.docx"
        return out_path
    return input_path.with_suffix(".docx")


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")
