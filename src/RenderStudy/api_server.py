from __future__ import annotations

import argparse
import io
import os
import secrets
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from .conversion_service import convert_input_file, convert_text_to_docx

app = FastAPI(title="RenderStudy API", version="1.0.0")

ALLOWED_EXTENSIONS = {".md", ".txt", ".docx"}
DOCX_REQUIRED_ENTRIES = {"[Content_Types].xml", "word/document.xml"}
MAX_DOCX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_DOCX_ENTRIES = 5000
MAX_ZIP_RATIO = 200.0


def _resolve_title_template() -> Path | None:
    env_path = os.environ.get("RENDERSTUDY_TITLE_TEMPLATE")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return p
    fallback = Path(__file__).resolve().parents[2] / "examples" / "титульник.docx"
    if fallback.exists():
        return fallback
    return None


def _build_multipart_docx_response(docx_path: Path, filename: str = "formatted.docx") -> Response:
    boundary = f"----RenderStudyBoundary{secrets.token_hex(16)}"
    payload = docx_path.read_bytes()
    headers = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n"
        "\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = headers + payload + tail
    return Response(content=body, media_type=f"multipart/form-data; boundary={boundary}")


def _unsupported(detail: str) -> HTTPException:
    return HTTPException(status_code=415, detail=detail)


def _validate_upload_file(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise _unsupported("Unsupported Media Type: only .md, .txt, .docx are accepted.")
    if ext == ".docx":
        _validate_docx_bytes(content)
    else:
        _validate_text_bytes(content, ext=ext)
    return ext


def _validate_text_bytes(content: bytes, *, ext: str) -> None:
    if content.startswith(b"PK\x03\x04"):
        raise _unsupported(f"Unsupported Media Type: {ext} does not match file signature.")
    if b"\x00" in content:
        raise _unsupported(f"Unsupported Media Type: {ext} appears to be binary.")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _unsupported(f"Unsupported Media Type: {ext} must be UTF-8 text.") from exc


def _validate_docx_bytes(content: bytes) -> None:
    if not content.startswith(b"PK\x03\x04"):
        raise _unsupported("Unsupported Media Type: .docx signature is invalid.")
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise _unsupported("Unsupported Media Type: .docx is not a valid ZIP container.") from exc

    infos = zf.infolist()
    if len(infos) > MAX_DOCX_ENTRIES:
        raise _unsupported("Unsupported Media Type: ZIP has too many entries.")

    names = {i.filename for i in infos}
    if not DOCX_REQUIRED_ENTRIES.issubset(names):
        raise _unsupported("Unsupported Media Type: required DOCX entries are missing.")

    total_uncompressed = 0
    for info in infos:
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
            raise _unsupported("Unsupported Media Type: archive uncompressed size is too large.")
        if info.compress_size > 0:
            ratio = info.file_size / info.compress_size
            if ratio > MAX_ZIP_RATIO:
                raise _unsupported("Unsupported Media Type: suspicious compression ratio (zip-bomb check).")


@app.post("/format")
async def format_endpoint(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    filename: str | None = Form(default=None),
) -> Response:
    if file is None and (text is None or not text.strip()):
        raise HTTPException(status_code=400, detail="Provide either form field 'file' or non-empty 'text'.")
    if file is not None and text is not None:
        raise HTTPException(status_code=400, detail="Send either 'file' or 'text', not both.")

    with tempfile.TemporaryDirectory(prefix="renderstudy_api_") as tmp:
        tmp_dir = Path(tmp)
        out_path = tmp_dir / "formatted.docx"
        title_template = _resolve_title_template()

        try:
            if file is not None:
                raw_name = file.filename or "input"
                original_name = os.path.basename(raw_name)
                if not original_name or original_name in {".", ".."}:
                    original_name = "input"
                content = await file.read()
                ext = _validate_upload_file(original_name, content)
                in_path = tmp_dir / original_name
                in_path.write_bytes(content)
                convert_input_file(
                    input_path=in_path,
                    output_path=out_path,
                    use_title_template=False,
                    title_template_path=title_template if ext in {".md", ".docx"} else None,
                )
                out_name = f"{Path(original_name).stem}_formatted.docx"
            else:
                if title_template is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Title template is missing. Set RENDERSTUDY_TITLE_TEMPLATE or provide examples/титульник.docx.",
                    )
                text_bytes = (text or "").encode("utf-8")
                _validate_text_bytes(text_bytes, ext=".txt")
                convert_text_to_docx(text=text or "", output_path=out_path, title_template_path=title_template)
                stem = Path(filename).stem if filename else "text"
                out_name = f"{stem}_formatted.docx"
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {exc}") from exc

        return _build_multipart_docx_response(out_path, filename=out_name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="RenderStudyAPI", description="HTTP API for RenderStudy formatting.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
