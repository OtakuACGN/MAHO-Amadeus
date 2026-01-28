import logging
from typing import List, Dict, Optional
from core.Script import Script

class Director:
    """
    导演类，负责统筹剧本演进、维护公共记忆，并进行意图识别和任务分发。
    """
    def __init__(self, manager):
        self.script = Script(world_view=manager.config.get("world_view", "这是一个虚拟人物互动的世界。"))
        self.intent_llm = manager.llm  # 默认使用配置中的 LLM 进行意图识别

    async def get_target_characters(self, user_input: str, character_names: List[str]) -> str:
        """
        根据备选角色列表和用户输入，让 AI 决定哪个角色应该回复，或者返回 'all' 表示广播给所有人。
        """
        char_list_str = ", ".join(character_names)
        prompt = (
            f"你是一个虚拟人物互动系统的导演。你的任务是分析用户的输入，并从给定的备选角色列表中选择出最适合回应的角色，或者如果需要广播给所有人，则返回 'all'。\n"
            f"你需要直接返回角色名称或 'all'，不要包含任何其他解释文字。\n\n"
            f"备选角色列表: [{char_list_str}]\n"
            f"用户输入的提问: \"{user_input}\"\n\n"
            f"请从列表中选择应当回复的角色名称（只能选择一个），或者返回 'all' 表示广播给所有人："
        )
        
        # 调用 LLM
        response = await self.intent_llm.generate(prompt)
        
        # 处理 AI 返回的字符串
        if not response:
            return character_names[0] if character_names else "all"

        response = response.strip()
        
        if response == "all":
            return "all"
        elif response in character_names:
            return response
        else:
            # 如果 AI 没按格式回，保底选第一个
            return character_names[0] if character_names else "all"

    async def dispatch_intent(self, user_input: str, character_names: List[str]) -> List[Dict]:
        """
        根据用户输入，生成分发指令。
        返回格式: [{"character": "name1", "text": "user_input"}, ...]
        """
        target = await self.get_target_characters(user_input, character_names)
        
        if target == "all":
            return [{"character": name, "text": user_input} for name in character_names]
        else:
            return [{"character": target, "text": user_input}]