# Telegram Crypto Alert Bot

This bot monitors whale wallets and new coin launches and sends alerts via Telegram.

## 🛠 Setup (Render or Railway)

0. **Python 3.13+**
   - This bot is tested with Python 3.13. Ensure your runtime uses Python 3.13 or later.

1. **Create a `.env` file** with your Telegram credentials and API keys:

```
TELEGRAM_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_channel_or_group
WATCHED_WALLETS=0xWallet1,0xWallet2
ETHERSCAN_API_KEY=your_etherscan_key
# Optional: use a QuickNode RPC endpoint instead of Etherscan
QUICKNODE_RPC_URL=https://polished-convincing-needle.quiknode.pro/191380b33f5482520c5310af01a12745e0c2a511/
```

2. **Deploy on [Render](https://render.com)**:
   - Click "New Web Service"
   - Connect your GitHub repo or upload this ZIP
  - Set environment variables: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `WATCHED_WALLETS`, `ETHERSCAN_API_KEY`, `QUICKNODE_RPC_URL`
   - Use build command: `pip install -r requirements.txt`
   - Use start command: `python main.py`

### Automatic Deployment

If you connect the service to GitHub, enable **Auto-Deploy** in the Render
dashboard. For custom workflows, create a **Deploy Hook** on Render and set the
URL as the `RENDER_DEPLOY_HOOK` secret in your repository. This project includes
a GitHub Actions workflow at `.github/workflows/render-deploy.yml` that will
trigger the hook on every push to the `main` branch.

3. **Deploy on [Railway](https://railway.app)**:
   - Create new project
   - Upload this ZIP or link GitHub repo
  - Set `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `WATCHED_WALLETS`, `ETHERSCAN_API_KEY`, and `QUICKNODE_RPC_URL` in Environment
   - Done!

## 📦 Included

- `main.py`: core bot logic
- `requirements.txt`: dependencies
  - Includes `python-telegram-bot` 22.1 for Python 3.13 compatibility
- `Procfile`: required for Render
- `.env.example`: token placeholder

## Decentralized Storage Options

### QuickNode

You can pin wallet data to IPFS using the QuickNode Storage add-on.

1. Create a QuickNode account and enable the **Storage** add-on.
2. Generate a storage token from your QuickNode dashboard.
3. Add `QUICKNODE_STORAGE_TOKEN=<your_token>` to your `.env` file.
4. The bot's helper function will send JSON data to QuickNode's IPFS API and
   return the resulting CID.

### BitHub (alternative)

If you prefer, you can store data on a BitHub endpoint. Set the following in
your `.env` file:

```bash
BITHUB_API_URL=https://example.com/store
BITHUB_API_TOKEN=your_token
```

The bot will send the JSON payload to this endpoint when QuickNode credentials
are not provided.


