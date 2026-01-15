import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

# Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# 安定実績のあるページ
TANAKA_URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

MAX_RETRY = 3
ATH_FILE = "ath_gold.txt"

def send_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        return
    
    content = f"<@{DISCORD_USER_ID}> {message}" if DISCORD_USER_ID else message
    data = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Discord notification sent successfully.")
    except Exception as e:
        print(f"Failed to send Discord: {e}")

def fetch_gold_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(TANAKA_URL, headers=headers, timeout=15)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3 and "金" in cols[0].get_text(strip=True):
                price_text = cols[1].get_text(strip=True)
                price_val = re.sub(r'\D', '', price_text)
                change_val = cols[2].get_text(strip=True)
                
                return int(price_val), change_val
        
        return None, None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None, None

def check_ath(current_price):
    ath = 26051
    if os.path.exists(ATH_FILE):
        try:
            with open(ATH_FILE, "r") as f:
                ath = int(f.read().strip())
        except: pass
    
    if current_price > ath:
        with open(ATH_FILE, "w") as f:
            f.write(str(current_price))
        return True
    return False

def main():
    print(f"Start fetching gold price at {datetime.datetime.now()}")
    
    # 成功したら即座に終了するように修正
    success = False
    for retry in range(MAX_RETRY + 1):
        price, change = fetch_gold_price()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if price:
            is_ath = check_ath(price)
            title = "🎊 【金】史上最高値更新‼️🚀" if is_ath else "📈 金価格情報"

            msg = (f"{title}\n"
                   f"【田中貴金属 公式サイト】\n"
                   f"日時: {now}\n"
                   f"店頭小売価格: **{price:,} 円**\n"
                   f"前日比: **{change}**\n\n"
                   f"🔗 公式: {TANAKA_URL}")

            send_discord(msg)
            success = True
            break  # ←ここ！成功したらリトライループを抜けます
        
        print(f"Retry {retry + 1}...")
        time.sleep(5)
    
    if not success:
        send_discord("⚠️ 金価格の取得に失敗しました。")

if __name__ == "__main__":
    main()
