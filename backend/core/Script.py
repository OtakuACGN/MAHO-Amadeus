import logging
from typing import List, Dict
import asyncio

class Script:
    """
    剧本类，负责维护公共上下文（对话历史）和世界观设置。
    同时作为演出调度的中心，维护台词队列。
    """
    def __init__(self, world_view: str = ""):
        self.world_view = world_view
        self.public_history: List[Dict[str, str]] = []  # 存储角色和用户的对话历史
        # 格式示例: {"role": "user/character_name", "content": "消息内容"}
        
        # 台词调度队列，存放正在排队等待演出的角色信息
        # 元素格式: {"character": "char_name"}
        self.line_queue = asyncio.Queue()

    def add_message(self, role: str, content: str):
        """添加一条消息到公共上下文"""
        self.public_history.append({"role": role, "content": content})
        # 限制历史记录长度，防止上下文爆炸
        if len(self.public_history) > 20:
            self.public_history.pop(0)

    async def register_line(self, character_name: str):
        """角色申请发言，注册到台词队列"""
        await self.line_queue.put({
            "character": character_name
        })
        logging.info(f"[Script] 角色 {character_name} 已加入演出队列")

    def clear(self):
        """清空公共上下文"""
        self.public_history = []
