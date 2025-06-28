import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Bot
from monitors.ethereum_monitor import EthereumMonitor
from wallet_discovery import discover_smart_wallets

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Channel or group ID
WATCHED_WALLETS = os.getenv("WATCHED_WALLETS", "").split(",")
DISCOVERY_REFRESH_MINUTES = int(os.getenv("DISCOVERY_REFRESH_MINUTES", "60"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
initial_wallets = [w.strip() for w in WATCHED_WALLETS if w.strip()]
if not initial_wallets:
    initial_wallets = discover_smart_wallets()
monitor = EthereumMonitor(initial_wallets)


def format_alert(event: dict) -> str:
    token = event["token_address"]
    wallet = event["wallet"]
    amount = event["amount"]
    tx = event["tx_hash"]
    return (
        f"\U0001f680 Whale {wallet} bought token {token}\n"
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


async def refresh_wallets():
    while True:
        wallets = discover_smart_wallets()
        if wallets:
            monitor.update_wallets(wallets)
            logger.info("Updated wallet list: %s", wallets)
        await asyncio.sleep(DISCOVERY_REFRESH_MINUTES * 60)


if __name__ == "__main__":
    if not monitor.wallets:
        logger.error(
            "No wallets configured. Set WATCHED_WALLETS or provide discovery settings"
        )
    else:
        asyncio.run(asyncio.gather(poll_whales(), refresh_wallets()))
