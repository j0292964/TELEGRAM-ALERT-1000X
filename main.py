import logging
import json
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
STORAGE_TOKEN = os.getenv("QUICKNODE_STORAGE_TOKEN")
STORAGE_URL = os.getenv("QUICKNODE_STORAGE_URL", "https://api.quicknode.com/ipfs/rest/v1/pin")
BITHUB_URL = os.getenv("BITHUB_API_URL")
BITHUB_TOKEN = os.getenv("BITHUB_API_TOKEN")
ETHPLORER_API_KEY = os.getenv("ETHPLORER_API_KEY", "freekey")
SMART_WALLET_ADDRESSES = os.getenv("SMART_WALLET_ADDRESSES", "")

logging.basicConfig(level=logging.INFO)


def get_wallet_info(address: str):
    """Fetch wallet information from Ethplorer."""
    url = f"https://api.ethplorer.io/getAddressInfo/{address}"
    params = {"apiKey": ETHPLORER_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error("Failed to fetch wallet info for %s: %s", address, e)
        return None


def format_wallet_info(data: dict) -> str:
    """Create a human readable summary of wallet info."""
    lines = []
    address = data.get("address")
    if address:
        lines.append(f"\ud83d\udce6 {address}")
    eth_balance = data.get("ETH", {}).get("balance")
    if eth_balance is not None:
        lines.append(f"ETH Balance: {eth_balance}")
    tokens = data.get("tokens", [])
    if tokens:
        lines.append("Top tokens:")
        for token in tokens[:5]:
            info = token.get("tokenInfo", {})
            symbol = info.get("symbol", "?")
            decimals = int(info.get("decimals", 0)) if info.get("decimals") else 0
            raw_balance = token.get("balance", 0)
            balance = raw_balance / (10 ** decimals) if decimals else raw_balance
            lines.append(f"- {symbol}: {balance}")
    return "\n".join(lines)


async def push_smart_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send configured smart wallet summaries to the chat."""
    if not SMART_WALLET_ADDRESSES:
        logging.info("No smart wallets configured")
        return
    for addr in SMART_WALLET_ADDRESSES.split(','):
        addr = addr.strip()
        if not addr:
            continue
        info = get_wallet_info(addr)
        if info:
            await update.message.reply_text(format_wallet_info(info))
        else:
            await update.message.reply_text(f"Failed to fetch data for {addr}")


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return info for a wallet address provided by the user."""
    if not context.args:
        await update.message.reply_text("Usage: /wallet <address>")
        return
    address = context.args[0]
    info = get_wallet_info(address)
    if info:
        await update.message.reply_text(format_wallet_info(info))
    else:
        await update.message.reply_text("Could not fetch wallet data")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot is running on Python 3.13!")
    # Example usage of decentralized storage
    sample_data = {"chat_id": update.effective_chat.id}
    cid = store_wallet_data(sample_data)
    if cid:
        await update.message.reply_text(f"Stored sample data with CID: {cid}")
    await push_smart_wallets(update, context)

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
    app.add_handler(CommandHandler("wallet", wallet))
    app.run_polling()
