import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

# Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# 取得先URL
GOLD_SITE_URL = "https://ja.goldpedia.org/"
TANAKA_URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

MAX_RETRY = 3
ATH_FILE = "ath.txt"

def send_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        return
    
    # eddieさんへのメンション付き
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
        res = requests.get(GOLD_SITE_URL, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.find_all("tr")
        for row in rows:
            row_text = row.get_text()
            if "田中貴金属" in row_text:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    # 小売価格を抽出（数字のみ）
                    raw_price = cols[1].get_text(strip=True)
                    price_text = re.sub(r'\D', '', raw_price) 
                    
                    # 前日比を賢く特定
                    # 全ての列の中から「+」か「-」が含まれる、または値が小さい列を探す
                    change_text = "不明"
                    for i in range(2, len(cols)):
                        val = cols[i].get_text(strip=True)
                        # 25,000円のような大きな数値（買取価格）は無視
                        clean_val = re.sub(r'[^-+0-9]', '', val)
                        if clean_val and -2000 < int(clean_val.replace('+', '')) < 2000:
                            change_text = val
                            break
                    
                    # それでも見つからない場合の予備ロジック
                    if change_text == "不明" and len(cols) >= 4:
                         change_text = cols[3].get_text(strip=True)

                    print(f"Found price: {price_text}, change: {change_text}")
                    return price_text, change_text
        
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
            
            if price_int > ath:
                write_ath(price_int)
                status_emoji = "🎊 史上最高値更新‼️🚀"
            else:
                status_emoji = "📈 金価格情報"

            msg = (f"{status_emoji}\n"
                   f"【田中貴金属】\n"
                   f"日時: {now}\n"
                   f"店頭小売価格: **{price_int:,} 円**\n"
                   f"前日比: **{change}**\n\n"
                   f"🔗 公式サイト: {TANAKA_URL}")

            send_discord(msg)
            return
        
        retry += 1
        if retry <= MAX_RETRY:
            print(f"Retry {retry} in 5 seconds...")
            time.sleep(5)
        else:
            print("Failed to fetch price after retries.")

if __name__ == "__main__":
    main()
