# Project Summary

- Automates tracking of smart "whale" wallets on Ethereum mainnet
- Finds wallets that:
  - Bought new coins early
  - Held for 20+ days
  - Achieved 1000x or greater profit
- Indexes and clusters wallets that buy and hold together
- Sends real-time alerts to a Telegram channel when 2+ smart whales buy/hold a new coin
- No social media, CEX, or non-ETH chains in current scope
- All blockchain data pulled from a QuickNode Ethereum mainnet endpoint
- All alerts and progress logs sent via Telegram using your provided token and channel ID
- Code is modular and easy to expand later to more chains or features
