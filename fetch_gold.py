import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")
TANAKA_URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"
MAX_RETRY = 2
ATH_FILE = "ath_gold.txt"
LAST_SENT_FILE = "last_sent_date.txt"

def send_discord(message):
    if not DISCORD_WEBHOOK_URL: return
    content = f"<@{DISCORD_USER_ID}> {message}" if DISCORD_USER_ID else message
    requests.post(DISCORD_WEBHOOK_URL, json={"content": content})

def fetch_gold_price():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(TANAKA_URL, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        
        # サイト上の「更新日付」を取得して、今日のものかチェックする
        # 田中貴金属のサイトから日付テキストを探す
        date_tag = soup.find("p", class_="date")
        if date_tag:
            site_date_str = date_tag.get_text(strip=True) # 例: "2026年1月17日"
            today_jp = datetime.datetime.now().strftime("%Y年%m月%d日")
            # 今日以外（土日など更新がない日）ならスキップ
            if today_jp not in site_date_str:
                print(f"Site date ({site_date_str}) is not today ({today_jp}). Skipping.")
                return None, None

        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3 and "金" in cols[0].get_text(strip=True):
                price_text = cols[1].get_text(strip=True)
                price_val = re.sub(r'\D', '', price_text)
                change_val = cols[2].get_text(strip=True)
                if not price_val or "不明" in change_val:
                    return None, None
                return int(price_val), change_val
        return None, None
    except:
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
    # 土日は実行自体をスキップ (0=月, 5=土, 6=日)
    if datetime.datetime.now().weekday() >= 5:
        print("Today is weekend. Skipping.")
        return

    # 本日通知済みかチェック
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, "r") as f:
            if f.read().strip() == today_str:
                print("Already sent today.")
                return

    price, change = fetch_gold_price()
    if price:
        is_ath = check_ath(price)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        title = "🎊 【金】史上最高値更新‼️🚀" if is_ath else "📈 金価格情報"
        msg = (f"{title}\n【田中貴金属 公式サイト】\n"
               f"日時: {now}\n店頭小売価格: **{price:,} 円**\n"
               f"前日比: **{change}**\n\n🔗 公式: {TANAKA_URL}")
        send_discord(msg)
        
        # その日のうちに2度送らないよう、即座に日付を保存
        with open(LAST_SENT_FILE, "w") as f:
            f.write(today_str)
    else:
        print("Price not updated or not today's price.")

if __name__ == "__main__":
    main()
