import asyncio
import logging
import os
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from monitors.ethereum_monitor import EthereumMonitor
from wallet_discovery import discover_smart_wallets
from storage import load_wallets, save_wallets

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
DISCOVERY_REFRESH_MINUTES = int(os.getenv("DISCOVERY_REFRESH_MINUTES", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_initial_wallets() -> list:
    wallets = load_wallets()
    if wallets:
        return wallets
    raw = os.getenv("WATCHED_WALLETS", "")
    wallets = re.split(r"[\s,]+", raw.strip()) if raw else []
    if not wallets:
        wallets = discover_smart_wallets()
    save_wallets(wallets)
    return wallets


monitor = EthereumMonitor(get_initial_wallets())


def format_alert(event: dict) -> str:
    token = event["token_address"]
    wallet = event["wallet"]
    amount = event["amount"]
    tx = event["tx_hash"]
    return (
        f"\U0001f680 Wallet {wallet} bought {token}\n"
        f"Amount: {amount}\nTx: https://etherscan.io/tx/{tx}"
    )


async def poll_whales(app: Application) -> None:
    while True:
        alerts = monitor.check_wallets()
        for alert in alerts:
            msg = format_alert(alert)
            try:
                await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
                logger.info("Sent alert: %s", msg)
            except Exception as e:
                logger.error("Failed to send alert: %s", e)
        await asyncio.sleep(POLL_INTERVAL)


async def refresh_wallets(app: Application) -> None:
    while True:
        wallets = discover_smart_wallets()
        if wallets:
            saved = load_wallets()
            merged = list({*saved, *wallets})
            save_wallets(merged)
            monitor.update_wallets(merged)
            logger.info("Updated wallet list: %s", merged)
        await asyncio.sleep(DISCOVERY_REFRESH_MINUTES * 60)


async def clone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /clone <wallet>")
        return
    wallet = context.args[0].lower()
    wallets = load_wallets()
    if wallet in wallets:
        await update.message.reply_text("Wallet already tracked.")
        return
    wallets.append(wallet)
    save_wallets(wallets)
    monitor.update_wallets(wallets)
    await update.message.reply_text(f"Tracking {wallet}")


async def unclone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /unclone <wallet>")
        return
    wallet = context.args[0].lower()
    wallets = load_wallets()
    if wallet not in wallets:
        await update.message.reply_text("Wallet not tracked.")
        return
    wallets.remove(wallet)
    save_wallets(wallets)
    monitor.update_wallets(wallets)
    await update.message.reply_text(f"Stopped tracking {wallet}")


def main() -> None:
    """Start the bot and run until interrupted."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials missing")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("clone", clone))
    app.add_handler(CommandHandler("unclone", unclone))

    # Schedule background tasks for polling and wallet discovery
    app.create_task(poll_whales(app))
    app.create_task(refresh_wallets(app))

    app.run_polling()


if __name__ == "__main__":
    main()
