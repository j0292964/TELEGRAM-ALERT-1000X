import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Bot
from monitors.ethereum_monitor import EthereumMonitor

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Channel or group ID
WATCHED_WALLETS = os.getenv("WATCHED_WALLETS", "").split(",")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
monitor = EthereumMonitor([w.strip() for w in WATCHED_WALLETS if w.strip()])


def format_alert(event: dict) -> str:
    token = event['token_address']
    wallet = event['wallet']
    amount = event['amount']
    tx = event['tx_hash']
    return (
        f"\U0001F680 Whale {wallet} bought token {token}\n"
        f"Amount: {amount}\nTx: https://etherscan.io/tx/{tx}"
    )


async def poll_whales():
    while True:
        alerts = monitor.check_wallets()
        for alert in alerts:
            msg = format_alert(alert)
            try:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
                logger.info("Sent alert: %s", msg)
            except Exception as e:
                logger.error("Failed to send alert: %s", e)
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if not monitor.wallets:
        logger.error("No wallets configured. Set WATCHED_WALLETS in environment" )
    else:
        asyncio.run(poll_whales())
