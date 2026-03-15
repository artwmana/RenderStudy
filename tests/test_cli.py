from pathlib import Path
from unittest.mock import patch

import pytest

from RenderStudy.cli import build_parser, main


def test_build_parser_valid_args():
    parser = build_parser()
    args = parser.parse_args(["input.md", "-o", "output.docx", "--verbose"])
    assert args.input == "input.md"
    assert args.output == "output.docx"
    assert args.verbose is True


def test_build_parser_missing_input(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    captured = capsys.readouterr()
    assert "the following arguments are required: input" in captured.err


@patch("RenderStudy.cli.convert_input_file")
@patch("RenderStudy.cli.resolve_output_path")
@patch("RenderStudy.cli.configure_logging")
def test_main_success(mock_configure_logging, mock_resolve_output_path, mock_convert_input_file, tmp_path):
    # Create a dummy input file
    input_file = tmp_path / "test_input.md"
    input_file.touch()

    # Mock resolve_output_path to return a known path
    expected_output = tmp_path / "test_output.docx"
    mock_resolve_output_path.return_value = expected_output

    # Run main with valid arguments
    main([str(input_file), "-o", str(expected_output), "--verbose"])

    # Verify the calls
    mock_configure_logging.assert_called_once_with(verbose=True)
    mock_resolve_output_path.assert_called_once_with(input_file, str(expected_output))
    mock_convert_input_file.assert_called_once_with(
        input_path=input_file,
        output_path=expected_output,
        use_title_template=True
    )


def test_main_file_not_found():
    with pytest.raises(FileNotFoundError, match="Input file not found: non_existent_file.md"):
        main(["non_existent_file.md"])
