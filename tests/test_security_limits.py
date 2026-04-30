import pytest
from fastapi.testclient import TestClient
from RenderStudy.api_server import app, MAX_TEXT_SIZE
from pathlib import Path

def test_large_text(tmp_path, monkeypatch):
    template = tmp_path / "title.docx"
    from tests.test_api_server import _make_title_template
    _make_title_template(template)
    monkeypatch.setenv("RENDERSTUDY_TITLE_TEMPLATE", str(template))

    client = TestClient(app)
    response = client.post(
        "/format",
        data={"text": "A" * (MAX_TEXT_SIZE + 1), "filename": "test"}
    )
    assert response.status_code == 413
