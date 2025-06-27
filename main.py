import logging
import json
import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
STORAGE_TOKEN = os.getenv("QUICKNODE_STORAGE_TOKEN")
STORAGE_URL = os.getenv("QUICKNODE_STORAGE_URL", "https://api.quicknode.com/ipfs/rest/v1/pin")
BITHUB_URL = os.getenv("BITHUB_API_URL")
BITHUB_TOKEN = os.getenv("BITHUB_API_TOKEN")

WALLET_FILE = "wallets.json"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is running on Python 3.13!")
    # Example usage of decentralized storage
    sample_data = {"chat_id": update.effective_chat.id}
    cid = store_wallet_data(sample_data)
    if cid:
        await update.message.reply_text(f"Stored sample data with CID: {cid}")


def load_long_term_wallets():
    """Return wallet addresses that haven't bought recently."""
    try:
        with open(WALLET_FILE, "r") as f:
            wallets = json.load(f)
    except Exception as e:
        logging.error("Failed to load wallets: %s", e)
        return []

    result = []
    now = datetime.utcnow().date()
    for wallet in wallets:
        buys = [datetime.fromisoformat(d).date() for d in wallet.get("buys", [])]
        if not buys:
            continue
        last_buy = max(buys)
        recent_buys = [d for d in buys if (now - d).days <= 30]
        if (now - last_buy).days > 30 and len(recent_buys) <= 1:
            result.append(wallet["address"])
    return result


async def longterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallets = load_long_term_wallets()
    if wallets:
        text = "\n".join(wallets)
        await update.message.reply_text(f"Long-term wallets:\n{text}")
    else:
        await update.message.reply_text("No long-term wallets found.")

def store_wallet_data(data: dict):
    """Persist JSON data using QuickNode or BitHub if configured."""
    if STORAGE_TOKEN:
        files = {"file": ("data.json", json.dumps(data))}
        headers = {"Authorization": f"Bearer {STORAGE_TOKEN}"}
        try:
            resp = requests.post(STORAGE_URL, files=files, headers=headers, timeout=10)
            resp.raise_for_status()
            cid = resp.json().get("cid")
            logging.info("Stored data on IPFS with CID %s", cid)
            return cid
        except Exception as e:
            logging.error("Failed to store data on QuickNode: %s", e)
            return None
    elif BITHUB_URL and BITHUB_TOKEN:
        headers = {"Authorization": f"Bearer {BITHUB_TOKEN}"}
        try:
            resp = requests.post(BITHUB_URL, json=data, headers=headers, timeout=10)
            resp.raise_for_status()
            result = resp.json().get("cid") or resp.json().get("hash")
            logging.info("Stored data on BitHub with id %s", result)
            return result
        except Exception as e:
            logging.error("Failed to store data on BitHub: %s", e)
            return None
    else:
        logging.warning("No storage service configured")
        return None

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("longterm", longterm))
    app.run_polling()
