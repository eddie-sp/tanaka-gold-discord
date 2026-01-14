import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def main():
    # 平日チェック
    if datetime.now().weekday() >= 5:
        return

    res = requests.get(URL, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # 店頭小売価格（税込）
    retail_price = soup.find("th", string="店頭小売価格（税込）") \
                       .find_next_sibling("td") \
                       .get_text(strip=True)

    # 小売価格 前日比
    diff_price = soup.find("th", string="小売価格 前日比") \
                     .find_next_sibling("td") \
                     .get_text(strip=True)

    today = datetime.now().strftime("%Y/%m/%d（%a）")

    arrow = "📈" if "+" in diff_price else "📉"

    message = (
        f"📅 {today}\n\n"
        f"💰 **店頭小売価格（税込）**\n"
        f"{retail_price}\n\n"
        f"📊 **小売価格 前日比**\n"
        f"{diff_price} {arrow}"
    )

    requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )

if __name__ == "__main__":
    main()
