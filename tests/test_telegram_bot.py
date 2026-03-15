import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from telegram import Update, Message, Document, File
from telegram.ext import ContextTypes

from RenderStudy.telegram_bot import start_handler, text_handler, document_handler

@pytest.fixture
def update_mock():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.reply_document = AsyncMock()
    # default IDs for work_prefix
    update.message.chat_id = 123
    update.message.message_id = 456
    return update

@pytest.fixture
def context_mock():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context

@pytest.mark.asyncio
async def test_start_handler(update_mock, context_mock):
    await start_handler(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_once()
    assert "Отправьте .md, .docx или просто текст" in update_mock.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_start_handler_no_message(update_mock, context_mock):
    update_mock.message = None
    await start_handler(update_mock, context_mock)
    # Should not crash, just return

@pytest.mark.asyncio
async def test_text_handler_no_message(update_mock, context_mock):
    update_mock.message = None
    await text_handler(update_mock, context_mock)
    # Should just return

@pytest.mark.asyncio
async def test_text_handler_empty_text(update_mock, context_mock):
    update_mock.message.text = "   "
    await text_handler(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_once_with("Пустой текст. Отправьте содержимое для конвертации.")

@pytest.mark.asyncio
@patch("RenderStudy.telegram_bot._resolve_title_template")
async def test_text_handler_no_template(mock_resolve, update_mock, context_mock):
    update_mock.message.text = "Some valid text"
    mock_resolve.return_value = None
    await text_handler(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_once_with("Не найден титульник. Укажите путь в RENDERSTUDY_TITLE_TEMPLATE.")

@pytest.mark.asyncio
@patch("RenderStudy.telegram_bot._resolve_title_template")
@patch("RenderStudy.telegram_bot.convert_text_to_docx")
@patch("RenderStudy.telegram_bot._persist_work")
async def test_text_handler_success(mock_persist, mock_convert, mock_resolve, update_mock, context_mock, tmp_path):
    update_mock.message.text = "Some valid text"
    mock_resolve.return_value = Path("dummy_template.docx")

    # We need to simulate the file creation because the handler does `with out_path.open("rb") as fp:`
    def fake_convert(text, out_path, title_template_path):
        out_path.write_text("dummy docx content")

    mock_convert.side_effect = fake_convert

    await text_handler(update_mock, context_mock)

    mock_convert.assert_called_once()
    mock_persist.assert_called_once()
    update_mock.message.reply_document.assert_called_once()
    assert update_mock.message.reply_document.call_args[1]["filename"] == "formatted.docx"

@pytest.mark.asyncio
async def test_document_handler_no_message(update_mock, context_mock):
    update_mock.message = None
    await document_handler(update_mock, context_mock)

@pytest.mark.asyncio
async def test_document_handler_no_document(update_mock, context_mock):
    update_mock.message.document = None
    await document_handler(update_mock, context_mock)

@pytest.mark.asyncio
async def test_document_handler_unsupported_ext(update_mock, context_mock):
    doc = MagicMock(spec=Document)
    doc.file_name = "test.pdf"
    update_mock.message.document = doc

    await document_handler(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_once_with("Поддерживаются только .md, .docx, .yaml, .yml")

@pytest.mark.asyncio
@patch("RenderStudy.telegram_bot._resolve_title_template")
async def test_document_handler_needs_template(mock_resolve, update_mock, context_mock):
    doc = MagicMock(spec=Document)
    doc.file_name = "test.md"

    tg_file = AsyncMock(spec=File)
    doc.get_file.return_value = tg_file
    update_mock.message.document = doc

    mock_resolve.return_value = None

    await document_handler(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_once_with("Нужен титульник. Укажите путь в RENDERSTUDY_TITLE_TEMPLATE.")

@pytest.mark.asyncio
@patch("RenderStudy.telegram_bot._resolve_title_template")
@patch("RenderStudy.telegram_bot.convert_input_file")
@patch("RenderStudy.telegram_bot._persist_work")
@patch("RenderStudy.telegram_bot._persist_markdown_dump")
async def test_document_handler_success_docx(mock_persist_md, mock_persist, mock_convert, mock_resolve, update_mock, context_mock):
    doc = MagicMock(spec=Document)
    doc.file_name = "test.docx"

    tg_file = AsyncMock(spec=File)
    doc.get_file.return_value = tg_file
    update_mock.message.document = doc

    mock_resolve.return_value = Path("dummy_template.docx")

    def fake_convert(in_path, out_path, use_title_template, title_template_path, extracted_md_path):
        out_path.write_text("dummy docx content")
        if extracted_md_path:
            extracted_md_path.write_text("dummy md content")

    mock_convert.side_effect = fake_convert

    await document_handler(update_mock, context_mock)

    mock_convert.assert_called_once()
    mock_persist.assert_called_once()
    mock_persist_md.assert_called_once()
    update_mock.message.reply_document.assert_called_once()
    assert update_mock.message.reply_document.call_args[1]["filename"] == "test_formatted.docx"

@pytest.mark.asyncio
@patch("RenderStudy.telegram_bot._resolve_title_template")
@patch("RenderStudy.telegram_bot.convert_input_file")
@patch("RenderStudy.telegram_bot._persist_work")
@patch("RenderStudy.telegram_bot._persist_markdown_dump")
async def test_document_handler_success_yaml(mock_persist_md, mock_persist, mock_convert, mock_resolve, update_mock, context_mock):
    doc = MagicMock(spec=Document)
    doc.file_name = "test.yaml"

    tg_file = AsyncMock(spec=File)
    doc.get_file.return_value = tg_file
    update_mock.message.document = doc

    mock_resolve.return_value = None # YAML doesn't strictly need a template

    def fake_convert(in_path, out_path, use_title_template, title_template_path, extracted_md_path):
        out_path.write_text("dummy docx content")

    mock_convert.side_effect = fake_convert

    await document_handler(update_mock, context_mock)

    mock_convert.assert_called_once()
    mock_persist.assert_called_once()
    mock_persist_md.assert_not_called()
    update_mock.message.reply_document.assert_called_once()
    assert update_mock.message.reply_document.call_args[1]["filename"] == "test_formatted.docx"
