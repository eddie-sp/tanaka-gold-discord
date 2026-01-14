import requests
from bs4 import BeautifulSoup
import datetime
import os
import time

# Discord Webhook URL とユーザーIDは Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# 取得するサイトURL
GOLD_SITE_URL = "https://ja.goldpedia.org/"  # Goldpedia の田中価格掲載ページ
TANAKA_URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

# 最大リトライ回数
MAX_RETRY = 3

# Discordに送信
def send_discord(message):
    if not DISCORD_WEBHOOK_URL or not DISCORD_USER_ID:
        raise RuntimeError("DISCORD_WEBHOOK_URL または DISCORD_USER_ID が未設定です")
    data = {
        "content": f"<@{DISCORD_USER_ID}> {message}"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    response.raise_for_status()

# Goldpedia から田中価格を取得
def fetch_gold_price():
    try:
        res = requests.get(GOLD_SITE_URL, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # テーブルから田中貴金属の行を検索
        table = soup.find("table")
        if not table:
            return None, None

        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if not cols:
                continue
            if "田中貴金属" in cols[0].get_text():
                price_text = cols[1].get_text(strip=True)
                change_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                return price_text, change_text

        return None, None
    except Exception as e:
        return None, None

def main():
    retry = 0
    notified_not_updated = False
    while retry <= MAX_RETRY:
        price, change = fetch_gold_price()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if price:
            msg = f"📈 更新された金価格（田中貴金属）\n日時: {now}\n店頭小売価格: {price}\n前日比: {change}\n🔗 公式サイト: {TANAKA_URL}"
            send_discord(msg)
            return
        else:
            if not notified_not_updated:
                msg = f"⏳ まだ価格が更新されていません（{now}）\n🔗 公式サイト: {TANAKA_URL}"
                send_discord(msg)
                notified_not_updated = True

        retry += 1
        if retry > MAX_RETRY:
            msg = f"⚠️ 最大リトライ回数に達しました（{now}）\n🔗 公式サイト: {TANAKA_URL}"
            send_discord(msg)
            return

        # 次のリトライまで待機（GitHub Actions では基本リトライは別スケジュール推奨ですが、待機しても可）
        time.sleep(5 * 60)  # 5分待機

if __name__ == "__main__":
    main()
