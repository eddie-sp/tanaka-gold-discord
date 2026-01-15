import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

# Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# ターゲット：田中貴金属 相場情報トップ
TANAKA_INDEX_URL = "https://gold.tanaka.co.jp/commodity/souba/index.php"

MAX_RETRY = 3
import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
import re

# Secrets から取得
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")

# 最も安定している「金価格推移」のページをターゲットに戻します
TANAKA_URL = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

MAX_RETRY = 3
ATH_FILE = "ath_gold.txt"

def send_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        return
    
    content = f"<@{DISCORD_USER_ID}> {message}" if DISCORD_USER_ID else message
    data = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Discord notification sent.")
    except Exception as e:
        print(f"Failed to send Discord: {e}")

def fetch_gold_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(TANAKA_URL, headers=headers, timeout=15)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        # 先ほど成功した「テーブルの2列目・3列目を抜く」ロジック
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3 and "金" in cols[0].get_text(strip=True):
                price_text = cols[1].get_text(strip=True)
                price_val = re.sub(r'\D', '', price_text) # 数字だけ抽出
                change_val = cols[2].get_text(strip=True) # 前日比
                
                return int(price_val), change_val
        
        return None, None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None, None

def check_ath(current_price):
    # 金の最高値だけをチェック
    ath = 26051 # 仮の最高値。これを超えたら通知。
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
    print(f"Start fetching gold price at {datetime.datetime.now()}")
    retry = 0
    while retry <= MAX_RETRY:
        price, change = fetch_gold_price()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if price:
            is_ath = check_ath(price)
            title = "🎊 【金】史上最高値更新‼️🚀" if is_ath else "📈 金価格情報"

            msg = (f"{title}\n"
                   f"【田中貴金属 公式サイト】\n"
                   f"日時: {now}\n"
                   f"店頭小売価格: **{price:,} 円**\n"
                   f"前日比: **{change}**\n\n"
                   f"🔗 公式: {TANAKA_URL}")

            send_discord(msg)
            return
        
        retry += 1
        time.sleep(5)
    
    send_discord("⚠️ 金価格の取得に失敗しました。")

if __name__ == "__main__":
    main()
def send_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        return
    
    content = f"<@{DISCORD_USER_ID}> {message}" if DISCORD_USER_ID else message
    data = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Discord notification sent.")
    except Exception as e:
        print(f"Failed to send Discord: {e}")

def fetch_all_metals():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(TANAKA_INDEX_URL, headers=headers, timeout=15)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        results = {}
        # 日本語名とプログラム用IDの紐付け
        targets = {"金": "gold", "プラチナ": "platinum", "銀": "silver"}
        
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                if name in targets:
                    price = re.sub(r'\D', '', cols[1].get_text(strip=True))
                    change = cols[2].get_text(strip=True)
                    results[targets[name]] = {
                        "display_name": name,
                        "price": int(price),
                        "change": change
                    }

        if len(results) >= 3:
            return results
        return None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

def check_ath(metal_id, current_price):
    """
    それぞれの金属ごとに最高値をチェックして更新する
    ファイル名は ath_gold.txt, ath_platinum.txt, ath_silver.txt となる
    """
    filename = f"ath_{metal_id}.txt"
    # デフォルト値（これを超えたら通知。初期値は低めに設定）
    initial_values = {"gold": 14000, "platinum": 6000, "silver": 200}
    
    ath = initial_values.get(metal_id, 10000)
    
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                ath = int(f.read().strip())
        except:
            pass
    
    if current_price > ath:
        with open(filename, "w") as f:
            f.write(str(current_price))
        return True, ath
    return False, ath

def main():
    print(f"Start fetching all metals at {datetime.datetime.now()}")
    retry = 0
    while retry <= MAX_RETRY:
        data = fetch_all_metals()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if data:
            update_messages = []
            is_any_ath = False
            
            # 各金属のメッセージ作成とATH判定
            for m_id in ["gold", "platinum", "silver"]:
                m_data = data[m_id]
                is_ath, old_ath = check_ath(m_id, m_data['price'])
                
                ath_label = ""
                if is_ath:
                    ath_label = " 🎊 **史上最高値更新‼️**"
                    is_any_ath = True
                
                emoji = {"gold": "🟡", "platinum": "⚪", "silver": "🔘"}[m_id]
                update_messages.append(
                    f"{emoji} **{m_data['display_name']}**{ath_label}\n"
                    f" └ 価格: **{m_data['price']:,} 円**\n"
                    f" └ 前日比: {m_data['change']}"
                )

            # メインタイトル
            title = "🚀 【史上最高値】新記録達成！" if is_any_ath else "📈 本日の貴金属相場情報"
            
            msg = (f"{title}\n"
                   f"日時: {now}\n\n"
                   + "\n\n".join(update_messages) + 
                   f"\n\n🔗 公式: {TANAKA_INDEX_URL}")

            send_discord(msg)
            return
        
        retry += 1
        time.sleep(5)
    
    send_discord("⚠️ 貴金属相場の取得に失敗しました。")

if __name__ == "__main__":
    main()
