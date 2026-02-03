import logging
import json
import asyncio
from typing import List, Dict, Optional
from core.Script import Script

class Director:
    """
    导演类，负责统筹剧本演进、维护公共记忆，并进行意图识别和任务分发。
    同时负责具体的演出编排（Orchestration），决定什么时候向前端发送哪个角色的输出。
    """
    def __init__(self, components):
        self.script = Script(world_view=components.config.get("world_view", "这是一个虚拟人物互动的世界。"))
        self.intent_llm = components.llm  # 默认使用配置中的 LLM 进行意图识别

    async def run_orchestrator(self, websocket, characters: Dict):
        """
        演出编排循环：
        不断从剧本的台词队列中提取任务，并将对应角色的输出流转发给前端。
        """
        while True:
            try:
                # 1. 从剧本领号 (等待下一位该说话的角色)
                line_info = await self.script.line_queue.get()
                char_name = line_info.get("character")
                character = characters.get(char_name)
                
                if not character:
                    logging.warning(f"[Director] 调度器收到未知角色: {char_name}")
                    self.script.line_queue.task_done()
                    continue

                logging.info(f"[Director] --- 开始播放演出: {char_name} ---")

                # 2. 独占式转发该角色的 output_queue 直到收到 end 信号
                while True:
                    item = await character.output_queue.get()
                    
                    try:
                        await websocket.send_text(json.dumps(item))
                    except Exception as e:
                        logging.error(f"[Director] 消息发送失败: {e}")
                        break

                    character.output_queue.task_done()

                    # 3. 如果是 end 信号，表示该角色本次发言结束
                    if item.get("type") == "end":
                        logging.info(f"[Director] --- 角色 {char_name} 发言结束 ---")
                        break
                
                self.script.line_queue.task_done()
                
                # 如果队列空了，说明本轮所有角色的戏都演完了
                if self.script.line_queue.empty():
                     await websocket.send_text(json.dumps({"type": "finish"}))

            except asyncio.CancelledError:
                logging.info("[Director] 演出编排器任务已取消")
                break
            except Exception as e:
                logging.error(f"[Director] 演出编排器异常: {e}")
                await asyncio.sleep(1)

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
        
        # 调用 LLM，收集异步生成器的完整结果
        response = ""
        async for chunk in self.intent_llm.generate(prompt):
            response += chunk
        
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
        根据用户输入，生成分发指令，并直接添加到剧本的台词队列。
        返回格式: [{"character": "name1", "text": "user_input"}, ...]
        """
        target = await self.get_target_characters(user_input, character_names)
        
        instructions = []
        if target == "all":
            instructions = [{"character": name, "text": user_input} for name in character_names]
        else:
            instructions = [{"character": target, "text": user_input}]
        
        # 直接将角色添加到剧本的台词队列
        for cmd in instructions:
            await self.script.register_line(cmd["character"])
        
        return instructions