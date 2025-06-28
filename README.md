# Telegram Crypto Alert Bot

This project tracks Ethereum whale wallets and alerts when multiple smart whales buy
and hold a new token. It communicates exclusively through Telegram.

## 🚀 Features

- Automatically scans Ethereum mainnet using a QuickNode endpoint
- Identifies wallets that bought new coins early, held 20+ days and achieved
  1000x profits
- Clusters wallets that buy and hold together
- Sends real-time alerts to a Telegram channel when two or more smart whales
  accumulate a new coin
- All alerts and progress logs are posted to Telegram
- Designed only for Ethereum mainnet (no CEX or social features yet)
- Code is modular and easy to expand later to more chains or features

## 🛠 Setup (Render or Railway)

1. **Create a `.env` file** with your credentials:

```
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_channel_id
QUICKNODE_URL=https://your-quicknode-endpoint
```

2. **Deploy on [Render](https://render.com)**:
   - Click "New Web Service"
   - Connect your GitHub repo or upload this ZIP
   - Set environment variables: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, and `QUICKNODE_URL`
   - Use build command: `pip install -r requirements.txt`
   - Use start command: `python main.py`

3. **Deploy on [Railway](https://railway.app)**:
   - Create new project
   - Upload this ZIP or link GitHub repo
   - Set `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, and `QUICKNODE_URL` in Environment
   - Done!

## 📦 Included

- `main.py`: core bot logic
- `requirements.txt`: dependencies
- `Procfile`: required for Render
- `.env.example`: example environment variables

## Example Telegram Alert

When the tracker detects coordinated buying by labeled whales, the alert shows
their history next to each address:

```
🚨 Smart whale activity detected!
Token: 0xNEWCOIN1234
Wallets:
0xWalletA - Dogecoin millionaire 1000x
0xWalletB - Shiba inu 100000x
```

