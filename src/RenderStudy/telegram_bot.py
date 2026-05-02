from __future__ import annotations

import argparse
from datetime import datetime
import logging
import os
import asyncio
import shutil
import tempfile
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .conversion_service import convert_input_file, convert_text_to_docx
from .utils import configure_logging

SUPPORTED_DOC_EXTS = {".md", ".docx", ".yaml", ".yml"}


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


def _storage_root() -> Path:
    env_path = os.environ.get("RENDERSTUDY_BOT_STORAGE")
    if env_path:
        root = Path(env_path).expanduser()
    else:
        root = Path.cwd() / "renderstudy_bot_storage"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _storage_dir(kind: str) -> Path:
    root = _storage_root()
    target = root / kind
    target.mkdir(parents=True, exist_ok=True)
    return target


def _work_prefix(update: Update) -> str:
    msg = update.message
    chat_id = msg.chat_id if msg else 0
    msg_id = msg.message_id if msg else 0
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{chat_id}_{msg_id}"


def _persist_work(kind: str, src_path: Path, out_path: Path, prefix: str) -> None:
    storage = _storage_dir(kind)
    src_target = storage / f"{prefix}_input{src_path.suffix.lower()}"
    out_target = storage / f"{prefix}_output.docx"
    shutil.copy2(src_path, src_target)
    shutil.copy2(out_path, out_target)


def _persist_markdown_dump(md_path: Path, prefix: str) -> None:
    storage = _storage_dir("md")
    target = storage / f"{prefix}_extracted.md"
    shutil.copy2(md_path, target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="RenderStudyBot",
        description="Telegram bot for formatting Markdown/DOCX/text to GOST DOCX.",
    )
    parser.add_argument("--token", type=str, default=None, help="Telegram bot token")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Отправьте .md, .docx или просто текст. Я верну готовый отформатированный .docx."
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not update.message.text:
        return

    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Пустой текст. Отправьте содержимое для конвертации.")
        return
    template = _resolve_title_template()
    if template is None:
        await update.message.reply_text(
            "Не найден титульник. Укажите путь в RENDERSTUDY_TITLE_TEMPLATE."
        )
        return

    with tempfile.TemporaryDirectory(prefix="renderstudy_bot_") as tmp:
        prefix = _work_prefix(update)
        text_path = Path(tmp) / "message_input.txt"
        out_path = Path(tmp) / "message_formatted.docx"

        def _process_text() -> bytes:
            text_path.write_text(text, encoding="utf-8")
            convert_text_to_docx(text, out_path, title_template_path=template)
            _persist_work("text", text_path, out_path, prefix)
            return out_path.read_bytes()

        doc_bytes = await asyncio.to_thread(_process_text)
        await update.message.reply_document(document=doc_bytes, filename="formatted.docx")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.document is None:
        return

    doc = update.message.document
    if doc.file_size is not None and doc.file_size > 20 * 1024 * 1024:
        await update.message.reply_text("Файл слишком большой. Максимальный размер - 20 МБ.")
        return

    raw_name = doc.file_name or "input"
    name = os.path.basename(raw_name)
    if not name or name in {".", ".."}:
        name = "input"
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_DOC_EXTS:
        await update.message.reply_text("Поддерживаются только .md, .docx, .yaml, .yml")
        return

    with tempfile.TemporaryDirectory(prefix="renderstudy_bot_") as tmp:
        prefix = _work_prefix(update)
        in_path = Path(tmp) / name
        out_name = f"{Path(name).stem}_formatted.docx"
        out_path = Path(tmp) / out_name
        extracted_md_path = Path(tmp) / "extracted_body.md"

        tg_file = await doc.get_file()
        await tg_file.download_to_drive(custom_path=str(in_path))

        template = _resolve_title_template()
        if suffix in {".md", ".docx"} and template is None:
            await update.message.reply_text(
                "Нужен титульник. Укажите путь в RENDERSTUDY_TITLE_TEMPLATE."
            )
            return
        template_for_convert = template if suffix in {".md", ".docx"} else None

        def _process_doc() -> bytes:
            convert_input_file(
                in_path,
                out_path,
                use_title_template=False,
                title_template_path=template_for_convert,
                extracted_md_path=extracted_md_path if suffix == ".docx" else None,
            )
            kind = "md" if suffix == ".md" else "docx" if suffix == ".docx" else "text"
            _persist_work(kind, in_path, out_path, prefix)
            if suffix == ".docx" and extracted_md_path.exists():
                _persist_markdown_dump(extracted_md_path, prefix)
            return out_path.read_bytes()

        doc_bytes = await asyncio.to_thread(_process_doc)
        await update.message.reply_document(document=doc_bytes, filename=out_name)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Telegram bot error: %s", context.error)


def main(argv: list[str] | None = None) -> None:
    # Load env from current working directory and project root so script works
    # even when started outside of repository root.
    load_dotenv(find_dotenv(filename=".env", usecwd=True), override=False)
    project_env = Path(__file__).resolve().parents[2] / ".env"
    if project_env.exists():
        load_dotenv(project_env, override=False)
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)

    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if args.verbose:
        logging.info(
            "Token source: %s",
            "--token" if args.token else ("TELEGRAM_BOT_TOKEN" if token else "missing"),
        )
    if not token:
        raise RuntimeError("Telegram token is required (--token or TELEGRAM_BOT_TOKEN).")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
