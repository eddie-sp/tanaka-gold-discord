import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

# Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# ターゲット：田中貴金属公式サイト
TANAKA_URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

MAX_RETRY = 3
ATH_FILE = "ath.txt"

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
        res.encoding = res.apparent_encoding # Shift_JIS対策
        soup = BeautifulSoup(res.text, "html.parser")

        # 画像のテーブル構造を解析
        # <tr><td>金</td><td>25,998 円</td><td>-53 円</td>...</tr> という構造を想定
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3 and "金" == cols[0].get_text(strip=True):
                # 小売価格 (25,998 円)
                price_text = cols[1].get_text(strip=True)
                price_val = re.sub(r'\D', '', price_text)
                
                # 前日比 (-53 円)
                change_val = cols[2].get_text(strip=True)
                
                print(f"Match Found! Price: {price_val}, Change: {change_val}")
                return price_val, change_val
        
        print("Log: '金' row not found in table.")
        return None, None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None, None

def read_ath():
    if os.path.exists(ATH_FILE):
        try:
            with open(ATH_FILE, "r") as f:
                return int(f.read().strip().replace(",", ""))
        except:
            pass
    return 26051 

def write_ath(value):
    with open(ATH_FILE, "w") as f:
        f.write(str(value))

def main():
    print(f"Start fetching gold price at {datetime.datetime.now()}")
    retry = 0
    while retry <= MAX_RETRY:
        price_str, change = fetch_gold_price()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if price_str:
            price_int = int(price_str)
            ath = read_ath()
            
            # 史上最高値の判定
            if price_int > ath:
                write_ath(price_int)
                status_emoji = "🎊 史上最高値更新‼️🚀"
            else:
                status_emoji = "📈 金価格情報"

            msg = (f"{status_emoji}\n"
                   f"【田中貴金属 公式サイト】\n"
                   f"日時: {now}\n"
                   f"店頭小売価格: **{price_int:,} 円**\n"
                   f"前日比: **{change}**\n\n"
                   f"🔗 公式: {TANAKA_URL}")

            send_discord(msg)
            return
        
        retry += 1
        print(f"Retry {retry} in 5 seconds...")
        time.sleep(5)
    
    send_discord("⚠️ 公式サイトの解析に失敗しました。")

if __name__ == "__main__":
    main()
