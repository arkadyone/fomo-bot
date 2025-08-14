# Fomo-bot — Daily Crypto Market Wrap  
_A white-label, open-source bot for Telegram/Slack/Discord, powered by CoinGecko MCP & Claude_
---
Hackathon note: Built for the [CoinGecko MCP Hackathon] as a working, open-source reference for daily crypto market summaries.
None today.
---

## 📌 Overview
**Looser Bot** delivers a **once-a-day** concise crypto market wrap with:
- **Market overview** (cap, 24h change, volume, BTC dominance)
- **Majors snapshot** (BTC/ETH/SOL)
- **Top gainers / losers**
- **Strange activity**
- A playful **FOMO & Takeaways** message from Claude

Designed as a **white-label, open-source** tool — rebrand and deploy it to your own Telegram channel, Slack, or Discord server.

---

## ✨ Features
- 🗓 **Daily scheduled post** — runs at your chosen time.
- 🪙 **Majors snapshot** — BTC, ETH, SOL with price, % change, range, volume.
- 📈 **Top movers** — top gainers and losers (24h).
- 🧐 **Strange activity** — detects unusual moves when the market is flat.
- 🔥 **Claude commentary** — short, witty, and supportive.
- 🛠 **White-label ready** — rename, rebrand, change tone.
- 🌐 **Multi-platform** — Telegram now, Slack/Discord adapters ready.
- 🆓 **Open source** — fork, audit, extend.

---

## 🛠 How It Works
1. **Fetch**  
   - Uses **CoinGecko MCP** for live data (via `mcp-remote` SSE).
   - Fallback to CoinGecko Pro REST API for reliability.

2. **Analyze**  
   - Calculates gainers/losers, majors snapshot, strange activity, FOMO moves.

3. **Generate commentary**  
   - Sends structured JSON to **Claude** for the “FOMO & Takeaways” section.
   - Optional token-specific notes.

4. **Deliver**  
   - Formats output (Telegram-safe HTML or plain text for Slack/Discord).
   - Posts to your configured channel.

---

## 🖼 Example Output (Telegram)
---
```text
🔥 FOMO & Takeaways
Missed the pump? Relax — momentum’s selective and liquidity’s patchy. Monday inside you says: small wins > hero trades.

📊 Market Overview
Cap $4,03T | 24h +0.9% | Vol $139B | BTC dom 58.4%

🪙 Majors
BTC: +1.7% ($118,733) range $116,494–$118,887 vol $35.3B
ETH: +0.2% ($4,228) range $4,172–$4,316 vol $33.9B
SOL: +0.6% ($181.9) range $178–$186 vol $6.5B

🚀 Top Gainers (24h)
Lido DAO (LDO) | +15.7% | $1.380000
Raydium (RAY) | +11.6% | $3.360000
Dog (DOG) | +11.1% | $0.003622

💀 Top Losers (24h)
Rekt (REKT) | -17.2% | $0.000001
DeXe (DEXE) | -7.0% | $7.830000
Pi (PI) | -6.5% | $0.391748

🧐 Strange Activity
```

📦 Installation
```code
git clone https://github.com/youruser/looser-bot
cd looser-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install and run MCP bridge:
``` code
npm install -g mcp-remote
mcp-remote --server https://mcp.pro-api.coingecko.com/sse
```
🚀 Usage

Run once:
```code
python main.py
```

Schedule daily (example crontab at 09:00):
```code
0 9 * * * /path/to/venv/bin/python /path/to/looser-bot/main.py
```
🗺 Roadmap

Slack/Discord adapters packaged by default

Interactive /ask mode (token Q&A via MCP + Claude)

News enrichment

Portfolio tracking mode

📜 License

MIT — free to use, modify, and distribute.


---

