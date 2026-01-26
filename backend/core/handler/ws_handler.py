from core.auth.login import AuthManager
from core.chat import handle_chat, process_char_queue, process_sentence_queue
from core.Character import Character
from starlette.websockets import WebSocketDisconnect
import logging
import asyncio
import json
import base64
from pathlib import Path
import sys

# 添加项目根路径
sys.path.append(str(Path(__file__).parent.parent.parent))


class WSHandler():
    """
    负责处理 WebSocket 连接，接收消息并通过 ComponentManager 实例进行处理，
    每个websocket连接对应一个 ComponentManager 实例，确保用户隔离。
    """

    def __init__(self):
        self.auth_manager = AuthManager()  # 用于验证 WebSocket 消息中的 token
        self.current_chat_task = None      # 记录当前正在运行的聊天任务
        self.characters = {}               # 存储当前连接的所有角色实例
        self.character_tasks = []          # 存储所有角色的后台处理任务

    def init_characters(self, manager):
        """初始化角色列表"""
        char_configs = manager.config.get("characters", [])
        if not char_configs:
            # 如果没有配置角色，使用默认配置创建一个默认角色
            logging.warning("未在配置中找到角色定义，使用默认角色")
            default_config = {
                "system_prompt": manager.config.get("llm", {}).get("system_prompt", ""),
                "tts_config": {}
            }
            self.characters["maho"] = Character("maho", default_config)
        else:
            for conf in char_configs:
                name = conf.get("name")
                if name:
                    self.characters[name] = Character(name, conf)

    async def interrupt_chat(self, websocket, manager):
        """
        中断当前的聊天逻辑：取消 LLM 任务，清空所有角色的队列，发送结束信号
        """
        # 断开/取消 LLM 任务
        if self.current_chat_task and not self.current_chat_task.done():
            self.current_chat_task.cancel()
            try:
                await self.current_chat_task
            except asyncio.CancelledError:
                logging.info("LLM 生成任务已成功取消")
            except Exception as e:
                logging.error(f"取消任务时出错: {e}")
            finally:
                self.current_chat_task = None

        # 清空所有角色的队列
        for char_name, character in self.characters.items():
            # 清空消息队列 (字符流)
            while not character.message_queue.empty():
                try:
                    character.message_queue.get_nowait()
                    character.message_queue.task_done()
                except asyncio.QueueEmpty:
                    break

            # 清空句子队列 (TTS)
            while not character.sentence_queue.empty():
                try:
                    character.sentence_queue.get_nowait()
                    character.sentence_queue.task_done()
                except asyncio.QueueEmpty:
                    break

        # 发送结束标签
        await websocket.send_text(json.dumps({"type": "end"}))
        logging.info("已中断当前对话并清空所有队列")

    async def handle_ws(self, websocket, manager):
        """
        这里主要是接收数据
        """
        await websocket.accept()  # 必须先接受连接
        logging.info("WebSocket 连接已接受")
        
        # 1. 初始化角色
        self.init_characters(manager)
        logging.info(f"已加载角色: {list(self.characters.keys())}")

        # 初始化角色任务
        self.character_tasks = []
        for char_name, character in self.characters.items():
            char_task = asyncio.create_task(
                process_char_queue(manager, character, websocket))
            sentence_task = asyncio.create_task(
                process_sentence_queue(manager, character, websocket))
            self.character_tasks.extend([char_task, sentence_task])

        # 注意：这里不再需要手动 start ASR，由 send_audio 按需触发连接

        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)

                if msg.get("type") == "chat":
                    token = msg.get("token")
                    if not token or not self.auth_manager.verify_token(token):
                        await websocket.send_text(json.dumps({"type": "error", "msg": "未授权，请先登录"}))
                        continue
                    
                    # 获取目标角色
                    target_char_name = msg.get("character")
                    # 如果未指定，默认使用第一个
                    if not target_char_name and self.characters:
                        target_char_name = list(self.characters.keys())[0]
                    
                    character = self.characters.get(target_char_name)

                    if not character:
                         logging.warning(f"找不到目标角色: {target_char_name}")
                         await websocket.send_text(json.dumps({"type": "error", "msg": f"角色 {target_char_name} 不存在"}))
                         continue

                    # 创建新的聊天任务，不阻塞主循环以接收后续消息（如打断信号）
                    self.current_chat_task = asyncio.create_task(
                        handle_chat(websocket, manager, character, msg.get("data")))
                
                elif msg.get("type") == "interrupt":
                    # 显式接收到打断信号
                    await self.interrupt_chat(websocket, manager)
                
                elif msg.get("type") == "audio":
                    # 接收音频数据
                    token = msg.get("token")
                    if not token or not self.auth_manager.verify_token(token):
                        await websocket.send_text(json.dumps({"type": "error", "msg": "未授权，请先登录"}))
                        continue
                    
                    audio_data = msg.get("data")
                    is_final = msg.get("is_final", False)
                    target_char_name = msg.get("character")
                    
                    # 如果未指定，默认使用第一个
                    if not target_char_name and self.characters:
                        target_char_name = list(self.characters.keys())[0]
                    character = self.characters.get(target_char_name)
                    
                    try:
                        # 1. 发送数据 (如果 audio_data 为空但 is_final 为真，也需要调用以发送结束帧)
                        chunk = base64.b64decode(audio_data) if audio_data else b""
                        await manager.asr.send_audio(chunk, is_final=is_final)
                    except Exception as e:
                        logging.error(f"ASR 处理失败: {e}")

                    if is_final:
                        # 2. 从 ASR 获取最终文本 (ASRService 已经处理了 finish_audio 的逻辑)
                        user_text = manager.asr.get_result()
                        
                        if user_text and character:
                            logging.info(f"ASR 识别完成: {user_text} -> {character.name}")
                            self.current_chat_task = asyncio.create_task(
                                handle_chat(websocket, manager, character, user_text))
                        else:
                            logging.info("ASR 结束但没有有效文本，忽略")

        except WebSocketDisconnect:
            logging.info("WebSocket 已断开")
        finally:
            # 取消所有后台任务
            for task in self.character_tasks:
                task.cancel()
            
            if self.character_tasks:
                try:
                    await asyncio.wait(self.character_tasks, timeout=2)
                except asyncio.CancelledError:
                    pass
