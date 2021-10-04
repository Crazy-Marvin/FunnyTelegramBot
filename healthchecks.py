import requests
import os
import time

API_KEY = os.getenv("HEALTH_BOT_API")
ID = os.getenv("GROUP_ID")
MSG = ""

url = 'https://api.telegram.org/bot' + API_KEY + \
    '/sendMessage?chat_id=' + ID + '&parse_mode=Markdown&text='

while True:

    # Funny Telegram Bot
    try:
        requests.get(
            "https://hc-ping.com/17445703-16bb-402f-9632-c32ec7f9421d", timeout=30)
        MSG += "🟢 FUNNY BOT\n\n"
    except:
        MSG += "🔴 FUNNY BOT\n\n"

    requests.get(url=(url+MSG))
    MSG = ""
    time.sleep(3600)
