import asyncio
import time
from unittest.mock import MagicMock, AsyncMock
from src.RenderStudy.telegram_bot import document_handler, text_handler
from telegram import Update, Message, Document

async def simulate_event_loop_block():
    # We want to measure how much the event loop is blocked.
    # We can create a background task that constantly ticks and records the max delay.
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

    # Create mock update
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    document = MagicMock(spec=Document)

    update.message = message
    message.document = document
    document.file_name = "test.md"

    # Mock tg_file.download_to_drive
    tg_file = AsyncMock()
    document.get_file = AsyncMock(return_value=tg_file)

    # Create a dummy file for the bot to read
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tf:
        tf.write(b"# Test\n" * 1000)
        tf_path = tf.name

    async def mock_download(*args, **kwargs):
        import shutil
        target = kwargs.get('custom_path')
        shutil.copy2(tf_path, target)

    tg_file.download_to_drive = mock_download

    # Mock template resolution to avoid needing it
    import src.RenderStudy.telegram_bot as bot
    bot._resolve_title_template = MagicMock(return_value=None)

    message.reply_document = AsyncMock()
    message.reply_text = AsyncMock()

    # Create multiple tasks to run the handler concurrently
    start_time = time.monotonic()

    # Run 5 conversions concurrently
    tasks = [document_handler(update, None) for _ in range(5)]
    await asyncio.gather(*tasks)

    end_time = time.monotonic()

    running = False
    await ticker_task

    print(f"Total time: {end_time - start_time:.3f}s")
    print(f"Max event loop delay: {max_delay:.3f}s")

if __name__ == "__main__":
    asyncio.run(simulate_event_loop_block())
