
import requests
import time
import datetime
import telebot
import matplotlib.pyplot as plt
import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)
last_sent_time = 0
daily_count = 0
last_reset_day = datetime.datetime.utcnow().day

def get_binance_data():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/24hr")
        return response.json()
    except:
        return []

def filter_coins(data):
    filtered = []
    for coin in data:
        try:
            price = float(coin["lastPrice"])
            if 0.000000001 <= price <= 0.2:
                filtered.append({
                    "symbol": coin["symbol"],
                    "price": price,
                    "change": float(coin["priceChangePercent"]),
                    "low": float(coin["lowPrice"]),
                    "high": float(coin["highPrice"])
                })
        except:
            continue
    return filtered

def pick_signals(coins):
    return [c for c in coins if c["change"] <= -5]

def create_chart(symbol, low, high, current):
    levels = 6
    step = (high - low) / levels if high > low else 1
    levels_price = [low + step * i for i in range(levels + 1)]
    labels = [f"{p:.8f}" for p in reversed(levels_price)]
    values = [1 if current >= p else 0 for p in reversed(levels_price)]

    plt.figure(figsize=(4, 3))
    plt.barh(labels, values, color='green')
    plt.title(f"{symbol} দাম বিশ্লেষণ")
    plt.tight_layout()
    plt.axis("off")
    filename = f"{symbol}_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_signal(sig, count):
    price = sig["price"]
    buy = round(price * 0.996, 10)
    sell = round(price * 1.045, 10)
    profit = round((sell - buy) / buy * 100, 2)

    pstr = f"{price:.10f}".rstrip("0").rstrip(".")
    bstr = f"{buy:.10f}".rstrip("0").rstrip(".")
    sstr = f"{sell:.10f}".rstrip("0").rstrip(".")

    msg = (
        f"📊 সিগন্যাল নাম্বার: {count:02d}\n\n"
        f"🔻 কয়েন: {sig['symbol']}\n"
        f"💰 বর্তমান দাম: {pstr} USDT\n"
        f"📉 দাম কমেছে: {sig['change']}%\n\n"
        f"🟢 কেনার পরামর্শ: {bstr} USDT\n"
        f"🔴 বিক্রির লক্ষ্যমূল্য: {sstr} USDT\n\n"
        f"💸 সম্ভাব্য লাভ: প্রায় {profit}%+\n\n"
        f"📅 সময়: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
    )

    chart = create_chart(sig["symbol"], sig["low"], sig["high"], price)
    with open(chart, 'rb') as img:
        bot.send_photo(CHAT_ID, img, caption=msg)

def send_no_signal(count):
    msg = (
        f"📊 সিগন্যাল নাম্বার: {count:02d}\n"
        f"⚠️ এই সময়ে ভালো কোন কয়েন পাওয়া যায়নি।"
    )
    bot.send_message(CHAT_ID, msg)

while True:
    now = datetime.datetime.utcnow()
    if now.day != last_reset_day:
        daily_count = 0
        last_reset_day = now.day

    if time.time() - last_sent_time >= 1800:
        daily_count += 1
        data = get_binance_data()
        coins = filter_coins(data)
        signals = pick_signals(coins)

        if signals:
            send_signal(signals[0], daily_count)
        else:
            send_no_signal(daily_count)

        last_sent_time = time.time()

    time.sleep(5)
