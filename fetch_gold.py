import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

# Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# ターゲットは田中貴金属公式サイト
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
        # 田中貴金属のサイトは Shift_JIS なのでエンコーディングを設定
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 小売価格の取得 (ID: r_gold_k で指定されている場合が多い)
        # サイト内のテーブルから「金」の「小売価格」行を特定
        price_val = None
        change_val = "変動なし"

        # 金の小売価格が記載されているクラスや要素を検索
        # 田中貴金属のサイト構造：<div id="retail_price"> 内の価格を取得
        target_box = soup.find("div", id="gold_price")
        if not target_box:
            # 代替：テーブルから探す
            rows = soup.find_all("tr")
            for row in rows:
                if "小売価格" in row.get_text() and "金" in row.get_text():
                    cols = row.find_all(["td", "th"])
                    for col in cols:
                        text = col.get_text(strip=True)
                        if "円" in text and len(text) > 2:
                            price_val = re.sub(r'\D', '', text)
                            break
        else:
            price_text = target_box.get_text(strip=True)
            price_val = re.sub(r'\D', '', price_text)

        # 2. 前日比の取得
        # クラス名 "price_up" (赤) や "price_down" (青) を探す
        change_element = soup.find(class_=re.compile("price_up|price_down|price_flat"))
        if change_element:
            change_val = change_element.get_text(strip=True)
        else:
            # テキストから「前日比」という文字の次にある要素を探す
            change_label = soup.find(string=re.compile("前日比"))
            if change_label:
                change_val = change_label.find_next().get_text(strip=True)

        if price_val:
            print(f"Found price: {price_val}, change: {change_val}")
            return price_val, change_val
        
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
                   f"【田中貴金属 公式】\n"
                   f"日時: {now}\n"
                   f"店頭小売価格: **{price_int:,} 円**\n"
                   f"前日比: **{change}**\n\n"
                   f"🔗 公式サイト: {TANAKA_URL}")

            send_discord(msg)
            return
        
        retry += 1
        print(f"Retry {retry} in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()
