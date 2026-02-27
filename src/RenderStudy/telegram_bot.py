from __future__ import annotations

import argparse
import logging
import os
import tempfile
from pathlib import Path

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
        out_path = Path(tmp) / "message_formatted.docx"
        convert_text_to_docx(text, out_path, title_template_path=template)
        with out_path.open("rb") as fp:
            await update.message.reply_document(document=fp, filename="formatted.docx")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.document is None:
        return

    doc = update.message.document
    name = doc.file_name or "input"
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_DOC_EXTS:
        await update.message.reply_text("Поддерживаются только .md, .docx, .yaml, .yml")
        return

    with tempfile.TemporaryDirectory(prefix="renderstudy_bot_") as tmp:
        in_path = Path(tmp) / name
        out_name = f"{Path(name).stem}_formatted.docx"
        out_path = Path(tmp) / out_name

        tg_file = await doc.get_file()
        await tg_file.download_to_drive(custom_path=str(in_path))

        template = _resolve_title_template()
        if suffix == ".md" and template is None:
            await update.message.reply_text(
                "Для .md нужен титульник. Укажите путь в RENDERSTUDY_TITLE_TEMPLATE."
            )
            return
        use_template = suffix == ".md" and template is not None
        convert_input_file(
            in_path,
            out_path,
            use_title_template=False,
            title_template_path=template if use_template else None,
        )
        with out_path.open("rb") as fp:
            await update.message.reply_document(document=fp, filename=out_name)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Telegram bot error: %s", context.error)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)

    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN")
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
