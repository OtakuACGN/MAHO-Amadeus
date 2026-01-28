from core.auth.login import AuthManager
from core.Character import Character
from core.Director import Director
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
        self.character_tasks = []          # 存储所有角色的输出监听任务

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
            self.characters["maho"] = Character("maho", default_config, manager)
        else:
            for conf in char_configs:
                name = conf.get("name")
                if name:
                    self.characters[name] = Character(name, conf, manager)

    async def _forward_character_output(self, websocket, character):
        """
        监听角色的输出队列，并将结果实时转发到 WebSocket
        """
        while True:
            try:
                result = await character.output_queue.get()
                await websocket.send_text(json.dumps(result))
                character.output_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[{character.name}] 分发输出失败: {e!r}")

    async def _send_error(self, websocket, msg):
        """发送错误消息给客户端"""
        await websocket.send_text(json.dumps({"type": "error", "msg": msg}))

    def _validate_token(self, msg):
        """验证消息中的 token"""
        token = msg.get("token")
        return token and self.auth_manager.verify_token(token)

    async def interrupt_chat(self, websocket, manager):
        """
        中断当前的聊天逻辑：取消角色推理任务，并通知所有角色中断自己的处理
        """
        # 取消当前的推理任务 (Director 驱动的任务)
        if self.current_chat_task and not self.current_chat_task.done():
            self.current_chat_task.cancel()
            try:
                await self.current_chat_task
            except asyncio.CancelledError:
                logging.info("推理任务已成功取消")
            finally:
                self.current_chat_task = None

        # 通知所有角色进行内部中断逻辑
        for name, character in self.characters.items():
            await character.interrupt()

        # 发送结束标签通知前端清理状态
        await websocket.send_text(json.dumps({"type": "end"}))
        logging.info("已中断当前对话并清理所有角色状态")

    def _create_asr_callback(self, websocket, manager):
        """创建 ASR 成功回调，改为主循环中通过导演分发指令"""
        async def on_asr_success(text):
            if text:
                logging.info(f"ASR 识别成功: {text}")
                available_chars = list(self.characters.keys())
                # 1. 由导演决定谁该说话
                instructions = await self.director.dispatch_intent(text, available_chars)
                # 2. 执行指令
                for cmd in instructions:
                    character = self.characters.get(cmd["character"])
                    if character:
                        self.current_chat_task = asyncio.create_task(character.chat(cmd["text"]))
            else:
                logging.info("ASR 识别结果为空")
        return on_asr_success

    async def _handle_audio(self, websocket, manager, msg):
        """处理语音/音频数据流"""
        # 更新 ASR 回调 (不再绑定特定角色)
        callback = self._create_asr_callback(websocket, manager)
        manager.asr.set_callback(callback)
            
        try:
            audio_data = msg.get("data")
            is_final = msg.get("is_final", False)
            chunk = base64.b64decode(audio_data) if audio_data else b""
            await manager.asr.send_audio(chunk, is_final=is_final)
        except Exception as e:
            logging.error(f"ASR 处理失败: {e}")

    async def handle_ws(self, websocket, manager):
        """
        这里主要是接收数据
        """
        await websocket.accept()  # 必须先接受连接
        logging.info("WebSocket 连接已接受")
        
        # 初始化导演
        self.director = Director(manager)

        # 初始化角色
        self.init_characters(manager)
        logging.info(f"已加载角色: {list(self.characters.keys())}")

        # 启动角色的输出转发监听任务
        self.character_tasks = []
        for char_name, character in self.characters.items():
            fwd_task = asyncio.create_task(self._forward_character_output(websocket, character))
            self.character_tasks.append(fwd_task)

        try:
            # 主循环：接收消息并处理
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                
                # 统一验证 token
                if not self._validate_token(msg):
                    await self._send_error(websocket, "未授权，请先登录")
                    continue
                
                msg_type = msg.get("type")

                if msg_type == "chat":
                    user_text = msg.get("data")
                    available_chars = list(self.characters.keys())
                    
                    # 1. 由导演决定谁该说话
                    instructions = await self.director.dispatch_intent(user_text, available_chars)
                    
                    # 2. 调用简化的 _handle_chat 执行指令
                    for cmd in instructions:
                        character = self.characters.get(cmd["character"])
                        if character:
                            self.current_chat_task = asyncio.create_task(character.chat(cmd["text"]))
                
                elif msg_type == "audio":
                    await self._handle_audio(websocket, manager, msg)
                
                elif msg_type == "interrupt":
                    await self.interrupt_chat(websocket, manager)

        except WebSocketDisconnect:
            logging.info("WebSocket 已断开")
        except Exception as e:
            logging.error(f"WebSocket 异常: {e}")
        finally:
            # 停止所有角色的内部后台任务
            for char in self.characters.values():
                await char.stop_tasks()

            # 取消所有输出监听任务
            for task in self.character_tasks:
                task.cancel()
            
            if self.character_tasks:
                try:
                    await asyncio.wait(self.character_tasks, timeout=2)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
