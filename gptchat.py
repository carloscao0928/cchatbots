import os
import random
import time
from typing import Dict, List, Optional, Any, Tuple
import requests
from dotenv import load_dotenv
from loguru import logger

class AIClient: 
    def __init__(self, config: Dict):
        self.name = config['name']
        self.url = config['url']
        self.headers = config['headers']
        self.model = config['model']
        self.parser = config['response_parser']
        self.enabled = config['enabled']

class DiscordChatBot:
    AI_CONFIGS = {
        'gpt': {
            'name': 'GPT-4',
            'url': 'https://api.gpt.ge/v1/chat/completions',
            'headers': lambda self: {'Authorization': f'Bearer {self.gpt_key}'},
            'model': 'gpt-4o',
            'response_parser': lambda resp: resp['choices'][0]['message']['content'],
            'env_var': 'GPT_KEY'
        },
        'deepseek': {
            'name': 'DeepSeek',
            'url': 'https://api.deepseek.com/chat/completions',
            'headers': lambda self: {'Authorization': f'Bearer {self.deepseek_key}'},
            'model': 'deepseek-chat',
            'response_parser': lambda resp: resp['choices'][0]['message']['content'],
            'env_var': 'DEEPSEEK_KEY'
        }
    }

    def __init__(self):
        self._load_config()
        self._setup_headers()
        self.ai_clients = self._init_ai_clients()

    def _load_config(self) -> None:
        load_dotenv() 
        try:
            self.token = os.getenv('DC_TOKEN')
            self.dc_id = os.getenv('YOUR_ID')
            self.is_wait = os.getenv('IS_WAIT', 'no').lower()
            self.my_demand = os.getenv('MY_DEMAND', '')
            self.language = os.getenv('LANGUAGE', 'chinese').lower()
            self.channel_id = os.getenv('CHANNEL_ID')
            self.active_ais = os.getenv('AI_PROVIDERS', 'gpt,deepseek').lower().split(',')
            self.max_loop = int(os.getenv('MAX_LOOP', '5'))
            self.min_sleep = int(os.getenv('MIN_SLEEP', '30'))
            self.max_sleep = int(os.getenv('MAX_SLEEP', '60'))
            self.is_wait_time = int(os.getenv('IS_WAIT_TIME', '300'))
            self._validate_config()
        except (ValueError, TypeError) as e:
            logger.error(f"Load Error: {str(e)}")
            raise

    def _validate_config(self) -> None:
        required = {
            'DC_TOKEN': self.token,
            'CHANNEL_ID': self.channel_id,
            'YOUR_ID': self.dc_id,
        }
        
        if missing := [k for k, v in required.items() if not v]:
            raise ValueError(f"Miss Configure: {', '.join(missing)}")

        if self.max_sleep < self.min_sleep:
            raise ValueError('min_sleep cannot more than max_sleep')

    def _init_ai_clients(self) -> List[AIClient]:
        clients = []
        for ai_name in self.active_ais:
            if ai_name not in self.AI_CONFIGS:
                logger.warning(f"{ai_name} Unknow AI Service, Skipped")
                continue
                
            config = self.AI_CONFIGS[ai_name]
            api_key = os.getenv(config['env_var'])
            
            if not api_key:
                logger.warning(f"{ai_name} Missing API Key, Skipped")
                continue
                
            setattr(self, f'{ai_name}_key', api_key)
            
            clients.append(AIClient({
                'name': config['name'],
                'url': config['url'],
                'headers': config['headers'](self),
                'model': config['model'],
                'response_parser': config['response_parser'],
                'enabled': True
            }))
            
        if not clients:
            raise ValueError("No AI Service Configure")
            
        return clients

    def _call_ai_api(self, client: AIClient, prompt: str) -> Optional[str]:
        payload = {
            "model": client.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.1,
            "max_tokens": 30
        }
        try:
            response = requests.post(
                client.url,
                headers=client.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return client.parser(response.json())
        except Exception as e:
            logger.error(f"{client.name} Request Failed: {str(e)}")
            return None

    def get_ai_response(self, prompt: str) -> Optional[str]:
        random.shuffle(self.ai_clients)
        
        for client in self.ai_clients:
            if not client.enabled:
                continue
            if response := self._call_ai_api(client, prompt):
                return response
            logger.warning(f"{client.name} 服务不可用，尝试下一个...")
        return None

    def run(self):
        success_count = 0
        while success_count < self.max_loop:
            if not (messages := self.get_history()):
                logger.error("Retrieve history message failed, wait for retry...")
                time.sleep(30)
                continue

            prompt, can_reply = self._build_prompt(messages)
            
            if not can_reply:
                logger.info("当前不符合回复条件，等待中...")
                time.sleep(self.is_wait_time)
                continue

            if not (response := self.get_ai_response(prompt)):
                logger.error("所有AI服务均不可用")
                time.sleep(60)
                continue
                
            formatted = self._format_response(response)
            if self.send_message(formatted):
                logger.success(f"消息发送成功: {formatted}")
                success_count += 1
            else:
                logger.error("消息发送失败")

            delay = random.randint(self.min_sleep, self.max_sleep)
            logger.info(f"下次操作将在 {delay} 秒后继续...")
            time.sleep(delay)
        logger.success(f"已完成 {self.max_loop} 次对话任务")

def main():
    try:
        bot = DiscordChatBot()
        bot.run()
    except Exception as e:
        logger.critical(f"程序崩溃: {str(e)}")
        raise

if __name__ == '__main__':
    main()
