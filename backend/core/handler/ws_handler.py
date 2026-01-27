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

    async def _send_error(self, websocket, msg):
        """发送错误消息给客户端"""
        await websocket.send_text(json.dumps({"type": "error", "msg": msg}))

    def _validate_token(self, msg):
        """验证消息中的 token"""
        token = msg.get("token")
        return token and self.auth_manager.verify_token(token)

    def _get_target_character(self, msg):
        """获取目标角色，若未指定则使用第一个可用角色"""
        target_char_name = msg.get("character")
        if not target_char_name and self.characters:
            target_char_name = list(self.characters.keys())[0]
        
        character = self.characters.get(target_char_name)
        return character, target_char_name

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

    async def _handle_chat(self, websocket, manager, msg):
        """处理文本聊天请求"""
        if not self._validate_token(msg):
            await self._send_error(websocket, "未授权，请先登录")
            return

        character, char_name = self._get_target_character(msg)
        if not character:
            logging.warning(f"找不到目标角色: {char_name}")
            await self._send_error(websocket, f"角色 {char_name} 不存在")
            return

        # 创建新的聊天任务，不阻塞主循环以接收后续消息（如打断信号）
        self.current_chat_task = asyncio.create_task(
            handle_chat(websocket, manager, character, msg.get("data")))

    def _create_asr_callback(self, websocket, manager, character):
        """创建闭包形式的 ASR 成功回调"""
        async def on_asr_success(text):
            if text:
                logging.info(f"ASR 识别成功: {text}")
                # 这里的 websocket, manager, character 都是闭包捕获的外部变量
                await handle_chat(websocket, manager, character, text)
            else:
                logging.info("ASR 识别结果为空")
        return on_asr_success

    async def _handle_audio(self, websocket, manager, msg):
        """处理语音/音频数据流"""
        if not self._validate_token(msg):
            await self._send_error(websocket, "未授权，请先登录")
            return

        character, char_name = self._get_target_character(msg)
        # 更新 ASR 回调 (无需传递上下文对象)
        if character:
            callback = self._create_asr_callback(websocket, manager, character)
            manager.asr.set_callback(callback)
            
        try:
            audio_data = msg.get("data")
            is_final = msg.get("is_final", False)
            
            # 1. 发送数据 (如果 audio_data 为空但 is_final 为真，也需要调用以发送结束帧)
            chunk = base64.b64decode(audio_data) if audio_data else b""
            # 发送时如果是最后一帧，ASR Provider 内部会自动调用 set_callback 设置好的 callback
            await manager.asr.send_audio(chunk, is_final=is_final)
        except Exception as e:
            logging.error(f"ASR 处理失败: {e}")

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

        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "chat":
                    await self._handle_chat(websocket, manager, msg)
                
                elif msg_type == "audio":
                    await self._handle_audio(websocket, manager, msg)
                
                elif msg_type == "interrupt":
                    await self.interrupt_chat(websocket, manager)

        except WebSocketDisconnect:
            logging.info("WebSocket 已断开")
        except Exception as e:
            logging.error(f"WebSocket 异常: {e}")
        finally:
            # 取消所有后台任务
            for task in self.character_tasks:
                task.cancel()
            
            if self.character_tasks:
                try:
                    await asyncio.wait(self.character_tasks, timeout=2)
                except asyncio.CancelledError:
                    pass
