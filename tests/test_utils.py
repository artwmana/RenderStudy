import pytest
from src.RenderStudy.utils import sanitize_filename

def test_sanitize_filename_none():
    assert sanitize_filename(None) == "input"
    assert sanitize_filename(None, default="foo") == "foo"

def test_sanitize_filename_empty():
    assert sanitize_filename("") == "input"
    assert sanitize_filename("", default="foo") == "foo"

def test_sanitize_filename_dot():
    assert sanitize_filename(".") == "input"
    assert sanitize_filename("..") == "input"

def test_sanitize_filename_normal():
    assert sanitize_filename("foo.txt") == "foo.txt"
    assert sanitize_filename("my-file_name 123.md") == "my-file_name 123.md"

def test_sanitize_filename_posix_traversal():
    assert sanitize_filename("../foo.txt") == "foo.txt"
    assert sanitize_filename("../../foo.txt") == "foo.txt"
    assert sanitize_filename("/etc/passwd") == "passwd"
    assert sanitize_filename("some/nested/dir/file.txt") == "file.txt"

def test_sanitize_filename_windows_traversal():
    assert sanitize_filename("..\\foo.txt") == "foo.txt"
    assert sanitize_filename("..\\..\\foo.txt") == "foo.txt"
    assert sanitize_filename("C:\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("some\\nested\\dir\\file.txt") == "file.txt"

def test_sanitize_filename_mixed_traversal():
    assert sanitize_filename("../..\\foo.txt") == "foo.txt"
    assert sanitize_filename("C:\\path/to\\file.txt") == "file.txt"
