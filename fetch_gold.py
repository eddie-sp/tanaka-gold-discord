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
    p
