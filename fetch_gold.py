import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

# 田中貴金属 金価格ページ
URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

# 🔔 Discord あなたのユーザーID（ここを書き換える）
DISCORD_USER_ID = "ここにあなたのDiscordユーザーIDを入れる"


def text_or_fail(elem):
    if elem is None:
        return "取得失敗"
    return elem.get_text(" ", strip=True)


def find_price(soup, keyword):
    """
    <th>ラベル</th><td>値</td> 構造を前提に取得
    """
    th = soup.find("th", string=re.compile(keyword))
    if th is None:
        return "取得失敗"

    td = th.find_next_sibling("td")
    if td is None:
        return "取得失敗"

    return text_or_fail(td)


def main():
    # ページ取得
    res = requests.get(URL, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 価格取得
    retail_price = find_price(soup, "店頭小売価格")
    price_diff   = find_price(soup, "前日比")

    # 日付取得（取れなければ今日）
    date_elem = soup.find("span", class_=re.compile("date"))
    date_text = text_or_fail(date_elem)
    if date_text == "取得失敗":
        date_text = datetime.now().strftime("%Y/%m/%d")

    # Discord メンション
    mention = f"<@{DISCORD_USER_ID}>"

    # Discord メッセージ
    message = (
        f"{mention}\n"
        f"📅 {date_text}\n\n"
        f"💰 店頭小売価格（税込）\n"
        f"{retail_price}\n\n"
        f"📊 小売価格 前日比\n"
        f"{price_diff}"
    )

    # Webhook URL
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL が未設定です")

    # Discord送信
    r = requests.post(
        webhook,
        json={"content": message},
        timeout=10
    )
    r.raise_for_status()


if __name__ == "__main__":
    main()
