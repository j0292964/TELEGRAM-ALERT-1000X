import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from whale_tracker import WhaleTracker

import asyncio

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is running on Python 3.13!")

async def tracker_loop() -> None:
    """Background loop to periodically scan for whale activity."""
    tracker = WhaleTracker()
    while True:
        tracker.send_log("\u23f1 Checking for new whale activity")
        tracker.run()
        await asyncio.sleep(60)


async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    async with app:
        task = asyncio.create_task(tracker_loop())
        await app.start()
        await app.updater.start_polling()
        await app.updater.idle()
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
