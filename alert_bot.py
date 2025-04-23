
import asyncio
import requests
from datetime import datetime
from telegram import Bot
import os

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

TICKERS = ["TSLA", "SPY", "QQQ"]
CHECK_INTERVAL = 60

bot = Bot(token=TELEGRAM_TOKEN)

def fetch_options_flow(symbol):
    url = f"https://finnhub.io/api/v1/stock/option-chain?symbol={symbol}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    alerts = []

    for d in data.get("data", []):
        for option in d.get("options", []):
            volume = option.get("volume", 0)
            oi = option.get("openInterest", 1)
            premium = option.get("lastPrice", 0) * volume

            if oi == 0: oi = 1
            if volume > oi * 5 and premium > 1_000_000:
                alert = {
                    "type": option.get("type"),
                    "strike": option.get("strike"),
                    "expiration": option.get("expirationDate"),
                    "volume": volume,
                    "oi": oi,
                    "premium": round(premium, 2),
                    "symbol": symbol,
                    "bid": option.get("bid", "?"),
                    "ask": option.get("ask", "?")
                }
                alerts.append(alert)
    return alerts

async def send_alerts():
    while True:
        try:
            for symbol in TICKERS:
                alerts = fetch_options_flow(symbol)
                for a in alerts:
                    msg = f"[ALERT] Unusual {a['symbol']} Option Detected:\n" \
                          f"- Type: {a['type']}\n" \
                          f"- Strike: ${a['strike']}\n" \
                          f"- Exp: {a['expiration']}\n" \
                          f"- Volume: {a['volume']} (vs OI: {a['oi']})\n" \
                          f"- Premium: ${a['premium']}\n" \
                          f"- Bid/Ask: {a['bid']} / {a['ask']}\n" \
                          f"- Timestamp: {datetime.now().strftime('%H:%M:%S')}"
                    await bot.send_message(chat_id=CHAT_ID, text=msg)
        except Exception as e:
            print("Error:", e)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(send_alerts())
