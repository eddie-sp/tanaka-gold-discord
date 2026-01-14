import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"


def text_or_fail(elem):
    if elem is None:
        return "取得失敗"
    return elem.get_text(" ", strip=True)


def find_price(soup, keyword):
    td = soup.find("td", string=re.compile(keyword))
    if td is None:
        return "取得失敗"
    value_td = td.find_next_sibling("td")
    return text_or_fail(value_td)


def main():
    res = requests.get(URL, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    retail_price = find_price(soup, "店頭小売価格")
    price_diff   = find_price(soup, "前日比")

    date_elem = soup.find("span", class_=re.compile("date"))
    date_text = text_or_fail(date_elem)
    if date_text == "取得失敗":
        date_text = datetime.now().strftime("%Y/%m/%d")

    message = (
        f"📅 {date_text}\n\n"
        f"💰 店頭小売価格（税込）\n{retail_price}\n\n"
        f"📊 小売価格 前日比\n{price_diff}"
    )

    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL が未設定です")

    r = requests.post(webhook, json={"content": message}, timeout=10)
    r.raise_for_status()


if __name__ == "__main__":
    main()
