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

