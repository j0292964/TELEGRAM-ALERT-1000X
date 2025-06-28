# Telegram Crypto Alert Bot

This bot monitors whale wallets and new coin launches and sends alerts via Telegram.

## 🛠 Setup (Render or Railway)

1. **Create a `.env` file** with your Telegram Bot Token:

```
TELEGRAM_TOKEN=your_token_here
```

2. **Deploy on [Render](https://render.com)**:
   - Click "New Web Service"
   - Connect your GitHub repo or upload this ZIP
   - Set environment variable: `TELEGRAM_TOKEN`
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
   - Set `TELEGRAM_TOKEN` in Environment
   - Done!

## 📦 Included

- `main.py`: core bot logic
- `requirements.txt`: dependencies
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


