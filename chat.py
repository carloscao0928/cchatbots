import requests
import json
import random
import time

def get_random_message(channel_id, auth):
    headers = {
        "Authorization": auth,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=100"
    res = requests.get(url=url, headers=headers)
    result = json.loads(res.content)

    valid_messages = [msg['content'] for msg in result if not any(char in msg['content'] for char in ['<', '@', 'http', '?'])]
    if valid_messages:
        return random.choice(valid_messages)
    else:
        return None

def send_message(channel_id, auth, message):
    headers = {
        "Authorization": auth,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    data = {
        "content": message
    }
    res = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(res.content)

def chat(chanel_list, auth):
    while True:
        for channel_id in chanel_list:
            message = get_random_message(channel_id, auth)
            if message:
                send_message(channel_id, auth, message)
                break
        time.sleep(random.randrange(60, 61))

chanel_list = ['']
auth = ''
chat(chanel_list, auth)
