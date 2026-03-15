import logging
from pathlib import Path
from unittest.mock import patch

from RenderStudy.utils import configure_logging, read_markdown, resolve_output_path


def test_configure_logging_info():
    with patch("RenderStudy.utils.logging.basicConfig") as mock_basic_config:
        configure_logging(verbose=False)
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(levelname)s %(message)s",
        )


def test_configure_logging_debug():
    with patch("RenderStudy.utils.logging.basicConfig") as mock_basic_config:
        configure_logging(verbose=True)
        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="%(levelname)s %(message)s",
        )


def test_resolve_output_path_none_output():
    input_path = Path("some/dir/input_file.md")
    result = resolve_output_path(input_path, output=None)
    assert result == Path("some/dir/input_file.docx")


def test_resolve_output_path_file_output(tmp_path):
    input_path = Path("some/dir/input_file.md")
    # Output is just a path string (not an existing dir)
    output_str = str(tmp_path / "custom_output.docx")
    result = resolve_output_path(input_path, output=output_str)
    assert result == Path(output_str)


def test_resolve_output_path_dir_output(tmp_path):
    input_path = Path("some/dir/input_file.md")
    # Output is an existing directory
    output_dir = tmp_path / "outdir"
    output_dir.mkdir()
    result = resolve_output_path(input_path, output=str(output_dir))
    assert result == output_dir / "input_file.docx"


def test_read_markdown(tmp_path):
    # Create a temporary file with some content
    md_file = tmp_path / "test.md"
    content = "# Hello World\nThis is a test."
    md_file.write_text(content, encoding="utf-8")

    # Read the markdown file
    result = read_markdown(md_file)
    assert result == content
