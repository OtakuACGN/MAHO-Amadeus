import asyncio

class Character:
    """
    角色类，存储角色的状态、记忆和配置
    """
    def __init__(self, name: str, config: dict):
        self.name = name
        self.system_prompt = config.get("system_prompt", "")
        # 存储该角色特定的 TTS 配置（如参考音频路径、提示词等）
        self.tts_config = config.get("tts_config", {})
        
        self.history = []
        if self.system_prompt:
            self.history.append({"role": "system", "content": self.system_prompt})
            
        self.message_queue = asyncio.Queue()  # 字符流队列
        self.sentence_queue = asyncio.Queue() # 句子流队列
        
    def load_memory(self, memory: list):
        """加载历史记忆"""
        # 保留 system prompt
        if self.history and self.history[0]["role"] == "system":
            self.history = [self.history[0]] + memory
        else:
            self.history = memory

    def add_history_user(self, content: str):
        """添加用户消息到历史"""
        self.history.append({"role": "user", "content": content})

    def add_history_assistant(self, content: str):
        """添加助手消息到历史"""
        self.history.append({"role": "assistant", "content": content})
