from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from docx import Document as DocxDocument

from RenderStudy.api_server import app


def _make_title_template(path: Path) -> None:
    doc = DocxDocument()
    doc.add_paragraph("ТИТУЛЬНИК")
    doc.save(path)


def test_format_endpoint_text_returns_multipart_docx(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    client = TestClient(app)
    response = client.post(
        "/format",
        files={"text": (None, "# ВВЕДЕНИЕ\n\nТекст.")},
        data={"filename": "from_text"},
    )
    assert response.status_code == 200
    ctype = response.headers["content-type"]
    assert ctype.startswith("multipart/form-data; boundary=")
    assert b"filename=\"from_text_formatted.docx\"" in response.content
    assert b"application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.content


def test_format_endpoint_md_file_returns_multipart_docx(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    md_path = tmp_path / "in.md"
    md_path.write_text("# ВВЕДЕНИЕ\n\nТекст.", encoding="utf-8")

    client = TestClient(app)
    with md_path.open("rb") as fp:
        response = client.post("/format", files={"file": ("in.md", fp.read(), "text/markdown")})
    assert response.status_code == 200
    ctype = response.headers["content-type"]
    assert ctype.startswith("multipart/form-data; boundary=")
    assert b"filename=\"in_formatted.docx\"" in response.content


def test_format_endpoint_rejects_unsupported_extension(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    client = TestClient(app)
    response = client.post("/format", files={"file": ("bad.pdf", b"%PDF-1.7", "application/pdf")})
    assert response.status_code == 415


def test_format_endpoint_rejects_fake_docx_signature(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    client = TestClient(app)
    response = client.post("/format", files={"file": ("fake.docx", b"not-a-zip", "application/octet-stream")})
    assert response.status_code == 415


def test_format_endpoint_rejects_both_file_and_text(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    client = TestClient(app)
    response = client.post(
        "/format",
        files={"file": ("in.md", b"# H\n\ntext", "text/markdown"), "text": (None, "plain text")},
    )
    assert response.status_code == 400


def test_format_endpoint_rejects_empty_request(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    client = TestClient(app)
    response = client.post("/format", data={})
    assert response.status_code == 400

import io
import zipfile

def test_format_endpoint_rejects_docx_too_many_entries(monkeypatch):
    monkeypatch.setattr("RenderStudy.api_server.MAX_DOCX_ENTRIES", 1)

    # Create an in-memory zip file
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"content types")
        zf.writestr("word/document.xml", b"document")

    client = TestClient(app)
    response = client.post("/format", files={"file": ("test.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type: ZIP has too many entries."

def test_format_endpoint_rejects_docx_missing_required_entries():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("random_file.txt", b"random content")

    client = TestClient(app)
    response = client.post("/format", files={"file": ("test.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type: required DOCX entries are missing."

def test_format_endpoint_rejects_docx_too_large_uncompressed(monkeypatch):
    monkeypatch.setattr("RenderStudy.api_server.MAX_DOCX_UNCOMPRESSED_BYTES", 10)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b"A" * 15)
        zf.writestr("word/document.xml", b"document")

    client = TestClient(app)
    response = client.post("/format", files={"file": ("test.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type: archive uncompressed size is too large."

def test_format_endpoint_rejects_docx_suspicious_compression_ratio(monkeypatch):
    monkeypatch.setattr("RenderStudy.api_server.MAX_ZIP_RATIO", 1.1)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", b"A" * 1000)
        zf.writestr("word/document.xml", b"document")

    client = TestClient(app)
    response = client.post("/format", files={"file": ("test.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type: suspicious compression ratio (zip-bomb check)."
