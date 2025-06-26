import os
import time
import requests
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

def start(update, context):
    update.message.reply_text("✅ Bot is active! Whale and radar systems coming soon.")

def check_wallets():
    # Placeholder logic for wallet scanner
    print("🔍 Scanning wallets for new tokens...")

def run_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    print("🚀 Bot is running...")
    while True:
        check_wallets()
        time.sleep(3600)  # Run hourly

if __name__ == "__main__":
    run_bot()
