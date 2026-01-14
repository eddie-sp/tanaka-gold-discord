name: Gold Price Notify

on:
  schedule:
    # JST 9:40, 9:50, 10:00, 10:10 → UTCに変換
    - cron: '40 0 * * *'
    - cron: '50 0 * * *'
    - cron: '0 1 * * *'
    - cron: '10 1 * * *'
  workflow_dispatch:

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4

      - name: Run python fetch_gold.py
        run: python fetch_gold.py
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          DISCORD_USER_ID: ${{ secrets.DISCORD_USER_ID }}
