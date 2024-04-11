import requests
import json
import random
import time

def get_context(auth,chanel_id):

    headr = {
        "Authorization": auth,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
    }
    chanel_id = random.choice(chanel_list)
    url = "https://discord.com/api/v9/channels/{}/messages?limit=100".format(chanel_id)
    print(url)
    res = requests.get(url=url, headers=headr)

    result = json.loads(res.content)
    result_list = []
    for context in result:
        if ('<') not in context['content'] :
            if ('@') not in context['content'] :
                if ('http') not in context['content']:
                    if ('?') not in context['content']:
                        result_list.append(context['content'])

    return random.choice(result_list)

def chat(chanel_list,authorization):
      header = {
          "Authorization": authorization,
          "Content-Type": "application/json",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
      }
      for chanel_id in chanel_list:
          msg = {
              "content": "卷起来",
              "nonce": "82329451214{}33232234".format(random.randrange(0, 1000000)),
              "tts": False,
          }
          url = "https://discord.com/api/v9/channels/{}/messages".format(chanel_id)
          try:
              res = requests.post(url=url, headers=header, data=json.dumps(msg))
              print(res.content)
          except:
              pass
          continue
      #time.sleep(random.randrange(10, 30))

if __name__ == "__main__":
    chanel_list = [""]
    authorization_list = ""
    while True:
        try:
            chat(chanel_list,authorization_list)
            sleeptime = 61
            time.sleep(sleeptime)
        except:
            break
