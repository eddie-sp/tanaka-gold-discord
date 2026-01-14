import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def extract_prices(soup):
    retail = None
    diff = None

    for tr in soup.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue

        label = th.get_text(strip=True)

        if "店頭小売価格" in label:
            retail = td.get_text(strip=True)
        elif "小売価格前日比" in label:
            diff = td.get_text(strip=True)

    return retail, diff

def main():
    # 平日チェック
    if datetime.now().weekday() >= 5:
        return

    res = requests.get(URL, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    retail_price, diff_price = extract_prices(soup)

    if not retail_price or not diff_price:
        raise RuntimeError("価格情報を取得できませんでした")

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
