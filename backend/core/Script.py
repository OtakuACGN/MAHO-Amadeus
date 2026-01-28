import logging
from typing import List, Dict

class Script:
    """
    剧本类，负责维护公共上下文（对话历史）和世界观设置。
    """
    def __init__(self, world_view: str = ""):
        self.world_view = world_view
        self.public_history: List[Dict[str, str]] = []  # 存储角色和用户的对话历史
        # 格式示例: {"role": "user/character_name", "content": "消息内容"}

    def add_message(self, role: str, content: str):
        """添加一条消息到公共上下文"""
        self.public_history.append({"role": role, "content": content})
        # 限制历史记录长度，防止上下文爆炸
        if len(self.public_history) > 20:
            self.public_history.pop(0)

    def get_public_context(self) -> str:
        """获取格式化后的公共上下文字符串，供 LLM 参考"""
        context_lines = []
        if self.world_view:
            context_lines.append(f"世界观设置: {self.world_view}")
        
        context_lines.append("近期对话记录:")
        for msg in self.public_history:
            context_lines.append(f"{msg['role']}: {msg['content']}")
        
        return "\n".join(context_lines)

    def clear(self):
        """清空公共上下文"""
        self.public_history = []
