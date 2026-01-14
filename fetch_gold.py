import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"


def safe_text(elem):
    """要素が取れない場合でも落ちないようにする"""
    return elem.get_text(strip=True) if elem else "取得失敗"


def main():
    # ページ取得
    res = requests.get(URL, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 「店頭小売価格（税込）」を探す
    retail_label = soup.find("td", string="店頭小売価格（税込）")
    retail_price = safe_text(
        retail_label.find_next_sibling("td") if retail_label else None
    )

    # 「小売価格 前日比」を探す
    diff_label = soup.find("td", string="小売価格 前日比")
    price_diff = safe_text(
        diff_label.find_next_sibling("td") if diff_label else None
    )

    # 日付（ページ内の日付 or 今日）
    date_elem = soup.find("span", class_="date")
    date_text = safe_text(date_elem)

    if date_text == "取得失敗":
        date_text = datetime.now().strftime("%Y/%m/%d")

    # Discord メッセージ作成
    message = (
        f"📅 {date_text}\n\n"
        f"💰 店頭小売価格（税込）\n"
        f"{retail_price}\n\n"
        f"📊 小売価格 前日比\n"
        f"{price_diff}"
    )

    # Discord Webhook
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL が設定されていません")

    payload = {
        "cont
