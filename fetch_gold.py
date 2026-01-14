import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"


def safe_text(elem):
    return elem.get_text(strip=True) if elem else "取得失敗"


def find_value_by_label(soup, label_text):
    label = soup.find("td", string=re.compile(label_text))
    if not label:
        return "取得失敗"
    value_td = label.find_next_sibling("td")
    return safe_text(value_td)


def main():
    res = requests.get(URL, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    retail_price = find_value_by_label(soup, "店頭小売価格")
    price_diff   = find_value_by_label(soup, "前日比")

    date_elem = soup.find("span", class_="date")
    date_text = safe_text(date_elem)
    if date_text == "取得失敗":
        date_text = datetime.now().strftime("%Y/%m/%d")

    message = (
        f"📅 {date_text}\n\n"
        f"💰 店頭小売価格（税込）\n{retail_price}\n\n"
        f"📊 小売価格 前日比\n{price_diff}"
    )

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL が設定されていません")

    r = requests.post(webhook_url, json={"content": message}, timeout=10)
    r.raise_for_status()


if __name__ == "__main__":
    main()
