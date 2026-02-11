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

                logging.info(f"[Director] --- 调度角色输出: {char_name} ---")

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
                        logging.info(f"[Director] --- 角色 {char_name} 输出调度完成 ---")
                        
                        # 将角色回复记入公共历史（从角色历史里偷最后一条）
                        if character.history:
                            last_msg = character.history[-1]
                            if last_msg.get("role") == "assistant":
                                self.script.add_message(character.name, last_msg["content"])
                        
                        break
                
                self.script.line_queue.task_done()
                
                # 如果队列空了，说明本轮所有角色的戏都演完了

            except asyncio.CancelledError:
                logging.info("[Director] 演出编排器任务已取消")
                break
            except Exception as e:
                logging.error(f"[Director] 演出编排器异常: {e}")
                await asyncio.sleep(1)

    async def remove_from_queue(self, character_name: str):
        """从台词队列中移除指定角色的待演出任务"""
        # asyncio.Queue 不支持直接删除，需要临时取出过滤
        temp_items = []
        removed = False
        
        while not self.script.line_queue.empty():
            try:
                item = self.script.line_queue.get_nowait()
                if item.get("character") == character_name and not removed:
                    removed = True
                    self.script.line_queue.task_done()
                else:
                    temp_items.append(item)
            except asyncio.QueueEmpty:
                break
        
        # 把保留的项重新放回队列
        for item in temp_items:
            await self.script.line_queue.put(item)
            self.script.line_queue.task_done()
        
        if removed:
            logging.info(f"[Director] 已将 {character_name} 从演出队列移除")

    async def dispatch_intent(self, user_input: str, character_names: List[str]) -> List[Dict]:
        """
        根据用户输入，让 AI 选择需要回复的角色列表，生成分发指令。
        返回格式: [{"character": "name1", "text": "user_input"}, ...]
        """
        self.script.add_message("user", user_input)
        
        if not character_names:
            return []
        
        # 构建提示词，让 AI 返回 JSON 数组格式
        char_list_str = ", ".join(character_names)
        prompt = (
            f"你是导演，分析用户输入，从备选角色中选择需要回复的角色。\n"
            f"备选角色: [{char_list_str}]\n"
            f"用户输入: \"{user_input}\"\n\n"
            f"以 JSON 数组格式返回角色名列表，如 ['maho'] 或 ['maho', 'mayuri']。"
        )
        
        # 调用 LLM 获取角色列表
        response = ""
        async for chunk in self.intent_llm.generate(prompt):
            response += chunk
        
        # 解析返回的角色列表
        targets = []
        if response:
            try:
                import json
                parsed = json.loads(response.strip())
                if isinstance(parsed, list):
                    targets = [name for name in parsed if name in character_names]
            except:
                # 解析失败，尝试简单匹配
                targets = [name for name in character_names if name in response]
        
        # 保底选一个
        if not targets:
            targets = [character_names[0]]
        
        # 生成分发指令并注册到台词队列
        instructions = [{"character": name, "text": user_input} for name in targets]
        for cmd in instructions:
            await self.script.register_line(cmd["character"])
        
        return instructions

    def get_situation_context(self) -> str:
        """
        生成当前情境上下文，供角色参考（不存入角色历史）。
        包含：世界观摘要 + 最近 5 轮公共对话。
        """
        parts = []
        
        # 世界观（限制长度）
        world_view = self.script.world_view
        if world_view:
            if len(world_view) > 100:
                world_view = world_view[:100] + "..."
            parts.append(f"世界观：{world_view}")
        
        # 最近 5 轮公共对话
        recent = self.script.public_history[-5:] if self.script.public_history else []
        if recent:
            parts.append("近期对话：")
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:50]  # 单条限制50字
                if len(msg.get("content", "")) > 50:
                    content += "..."
                parts.append(f"  {role}: {content}")
        
        return "\n".join(parts)