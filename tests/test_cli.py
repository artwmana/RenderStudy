import argparse
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from RenderStudy.cli import build_parser, main


def test_build_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "RenderStudy"


@patch("RenderStudy.cli.convert_input_file")
@patch("RenderStudy.cli.configure_logging")
def test_main_valid_input_implicit_output(mock_configure_logging, mock_convert_input_file, tmp_path):
    input_file = tmp_path / "input.md"
    input_file.write_text("dummy")

    main([str(input_file)])

    mock_configure_logging.assert_called_once_with(verbose=False)
    mock_convert_input_file.assert_called_once_with(
        input_path=input_file,
        output_path=tmp_path / "input.docx",
        use_title_template=True,
    )


@patch("RenderStudy.cli.convert_input_file")
@patch("RenderStudy.cli.configure_logging")
def test_main_valid_input_explicit_output(mock_configure_logging, mock_convert_input_file, tmp_path):
    input_file = tmp_path / "input.md"
    input_file.write_text("dummy")
    output_file = tmp_path / "output.docx"

    main([str(input_file), "-o", str(output_file)])

    mock_configure_logging.assert_called_once_with(verbose=False)
    mock_convert_input_file.assert_called_once_with(
        input_path=input_file,
        output_path=output_file,
        use_title_template=True,
    )


def test_main_input_not_found(tmp_path):
    input_file = tmp_path / "non_existent.md"

    with pytest.raises(FileNotFoundError, match=f"Input file not found: {re.escape(str(input_file))}"):
        main([str(input_file)])


@patch("RenderStudy.cli.convert_input_file")
@patch("RenderStudy.cli.configure_logging")
def test_main_verbose_flag(mock_configure_logging, mock_convert_input_file, tmp_path):
    input_file = tmp_path / "input.md"
    input_file.write_text("dummy")

    main([str(input_file), "--verbose"])

    mock_configure_logging.assert_called_once_with(verbose=True)
    mock_convert_input_file.assert_called_once_with(
        input_path=input_file,
        output_path=tmp_path / "input.docx",
        use_title_template=True,
    )
