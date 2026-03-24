import asyncio
import time
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
import tempfile
import shutil

async def simulate():
    from src.RenderStudy.telegram_bot import document_handler, text_handler
    from telegram import Update, Message, Document

    max_delay = 0
    running = True

    async def ticker():
        nonlocal max_delay
        last_time = time.monotonic()
        while running:
            await asyncio.sleep(0.01)
            now = time.monotonic()
            delay = now - last_time - 0.01
            if delay > max_delay:
                max_delay = delay
            last_time = now

    ticker_task = asyncio.create_task(ticker())

    # Create large dummy MD file that takes some time to parse
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tf:
        content = "# Title\n\n" + "Some paragraph text with **bold** formatting and *italics*.\n\n" * 5000
        tf.write(content.encode('utf-8'))
        tf_path = tf.name

    # Mock telegram context
    update = MagicMock()
    message = MagicMock()
    document = MagicMock()

    update.message = message
    message.document = document
    document.file_name = "test.md"

    tg_file = AsyncMock()
    document.get_file = AsyncMock(return_value=tg_file)

    async def mock_download(*args, **kwargs):
        target = kwargs.get('custom_path')
        if target:
            shutil.copy2(tf_path, target)

    tg_file.download_to_drive = mock_download

    # Needs a real or dummy title template for md to work.
    # Let's provide an empty .docx as a template so it doesn't fail fast
    template_path = "empty.docx"
    from docx import Document as DocxDocument
    doc = DocxDocument()
    doc.save(template_path)

    import src.RenderStudy.telegram_bot as bot
    bot._resolve_title_template = MagicMock(return_value=Path(template_path))

    message.reply_document = AsyncMock()
    message.reply_text = AsyncMock()

    start_time = time.monotonic()

    tasks = [document_handler(update, None) for _ in range(3)]
    await asyncio.gather(*tasks)

    end_time = time.monotonic()

    running = False
    await ticker_task

    print(f"Total time: {end_time - start_time:.3f}s")
    print(f"Max event loop delay: {max_delay:.3f}s")

if __name__ == "__main__":
    asyncio.run(simulate())
