import os
import random
import time
from typing import Dict, List, Optional, Any, Tuple
import requests
from dotenv import load_dotenv
from loguru import logger

class AIClient:
    """通用AI客户端配置类"""
    
    def __init__(self, config: Dict):
        self.name = config['name']
        self.url = config['url']
        self.headers = config['headers']
        self.model = config['model']
        self.parser = config['response_parser']
        self.enabled = config['enabled']

class DiscordChatBot:
    """Discord聊天机器人，支持多AI服务"""

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
        """加载所有环境变量配置"""
        load_dotenv()
        
        try:
            # 基础配置
            self.token = os.getenv('DC_TOKEN')
            self.channel_id = os.getenv('CHANNEL_ID')
            self.dc_id = os.getenv('YOUR_ID')
            
            # AI服务配置
            self.active_ais = os.getenv('AI_PROVIDERS', 'gpt,deepseek').lower().split(',')
            
            # 行为配置
            self.language = os.getenv('LANGUAGE', 'chinese').lower()
            self.max_loop = int(os.getenv('MAX_LOOP', '5'))
            self.min_sleep = int(os.getenv('MIN_SLEEP', '30'))
            self.max_sleep = int(os.getenv('MAX_SLEEP', '60'))
            self.is_wait = os.getenv('IS_WAIT', 'no').lower()
            self.is_wait_time = int(os.getenv('IS_WAIT_TIME', '300'))
            self.my_demand = os.getenv('MY_DEMAND', '')

            self._validate_config()

        except (ValueError, TypeError) as e:
            logger.error(f"配置加载错误: {str(e)}")
            raise

    def _validate_config(self) -> None:
        """验证配置有效性"""
        required = {
            'DC_TOKEN': self.token,
            'CHANNEL_ID': self.channel_id,
            'YOUR_ID': self.dc_id,
        }
        
        if missing := [k for k, v in required.items() if not v]:
            raise ValueError(f"缺少必要配置: {', '.join(missing)}")

        if self.max_sleep < self.min_sleep:
            raise ValueError('最大等待时间不能小于最小等待时间')

    def _init_ai_clients(self) -> List[AIClient]:
        """初始化启用的AI客户端"""
        clients = []
        
        for ai_name in self.active_ais:
            if ai_name not in self.AI_CONFIGS:
                logger.warning(f"未知的AI服务: {ai_name}，已跳过")
                continue
                
            config = self.AI_CONFIGS[ai_name]
            api_key = os.getenv(config['env_var'])
            
            if not api_key:
                logger.warning(f"未配置{ai_name}的API Key，已跳过")
                continue
                
            # 动态设置实例属性
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
            raise ValueError("没有可用的AI服务，请检查配置")
            
        return clients

    def _call_ai_api(self, client: AIClient, prompt: str) -> Optional[str]:
        """通用AI服务调用方法"""
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
            logger.error(f"{client.name} 请求失败: {str(e)}")
            return None

    def get_ai_response(self, prompt: str) -> Optional[str]:
        """随机选择一个AI服务获取响应"""
        random.shuffle(self.ai_clients)
        
        for client in self.ai_clients:
            if not client.enabled:
                continue
                
            if response := self._call_ai_api(client, prompt):
                return response
                
            logger.warning(f"{client.name} 服务不可用，尝试下一个...")
            
        return None

    # 以下保持其他方法不变（get_history, send_message, _build_prompt等）
    # ...

    def run(self):
        """运行主循环"""
        success_count = 0
        
        while success_count < self.max_loop:
            # 获取并处理历史消息
            if not (messages := self.get_history()):
                logger.error("获取消息失败，等待重试...")
                time.sleep(30)
                continue

            prompt, can_reply = self._build_prompt(messages)
            
            if not can_reply:
                logger.info("当前不符合回复条件，等待中...")
                time.sleep(self.is_wait_time)
                continue

            # 获取AI回复
            if not (response := self.get_ai_response(prompt)):
                logger.error("所有AI服务均不可用")
                time.sleep(60)
                continue
                
            # 格式化并发送消息
            formatted = self._format_response(response)
            if self.send_message(formatted):
                logger.success(f"消息发送成功: {formatted}")
                success_count += 1
            else:
                logger.error("消息发送失败")

            # 随机等待
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
