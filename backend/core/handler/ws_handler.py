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
    负责处理 WebSocket 连接，接收消息并通过 Components 实例进行处理，
    每个websocket连接对应一个 Components 实例，确保用户隔离。
    """

    def __init__(self):
        self.auth_manager = AuthManager()  # 用于验证 WebSocket 消息中的 token
        self.current_chat_task = None      # 记录当前正在运行的聊天任务
        self.orchestrator_task = None      # 演出编排任务
        self.characters = {}               # 存储当前连接的所有角色实例
        self.director = None               # 导演实例

    def init_characters(self, components):
        """初始化角色列表"""
        char_configs = components.config.get("characters", [])
        
        if not char_configs:
            # 如果没有配置角色，使用默认配置创建一个默认角色
            logging.warning("未在配置中找到角色定义，使用默认角色")
            default_config = {
                "system_prompt": components.config.get("llm", {}).get("system_prompt", ""),
                "tts_config": {}
            }
            self.characters["maho"] = Character("maho", default_config, components)
        else:
            for conf in char_configs:
                name = conf.get("name")
                if name:
                    self.characters[name] = Character(name, conf, components)

    def _validate_token(self, msg):
        """验证消息中的 token"""
        token = msg.get("token")
        return token and self.auth_manager.verify_token(token)

    async def interrupt_chat(self, websocket):
        """
        中断当前的聊天逻辑：取消角色推理任务，并通知所有角色中断自己的处理
        """
        # 清空剧本调度队列 (这是关键，防止后续排队的任务继续播放)
        if self.director and self.director.script:
             # asyncio.Queue 没有直接 clear 方法，只能循环 get
            q = self.director.script.line_queue
            while not q.empty():
                try:
                    q.get_nowait()
                    q.task_done()
                except asyncio.QueueEmpty:
                    break

        # 通知所有角色进行内部中断逻辑 (清空自身的 output_queue)
        for name, character in self.characters.items():
            await character.interrupt()

        # 发送结束标签通知前端清理状态
        await websocket.send_text(json.dumps({"type": "end"}))
        logging.info("已中断当前对话并清理所有角色状态")

    async def _dispatch_chat(self, user_text: str):
        """
        处理用户输入，由导演决定谁该说话，并并行触发角色的生成任务。
        这是 chat 和 ASR 的统一入口。
        """
        if not user_text:
            return
            
        available_chars = list(self.characters.keys())
        
        # 1. 由导演决定谁该说话
        instructions = await self.director.dispatch_intent(user_text, available_chars)
        
        # 2. 并行触发所有相关角色的生成任务
        for cmd in instructions:
            character = self.characters.get(cmd["character"])
            if character:
                # 这里的 create_task 会立即开始生成，发送给前端的信息会由导演负责
                self.current_chat_task = asyncio.create_task(character.chat(cmd["text"]))

    async def _handle_audio(self, components, msg):
        """处理语音/音频数据流"""
        # 设置回调：识别成功后直接走统一的文本处理逻辑
        components.asr.set_callback(self._dispatch_chat)
            
        try:
            audio_data = msg.get("data")
            is_final = msg.get("is_final", False)
            chunk = base64.b64decode(audio_data) if audio_data else b""
            await components.asr.send_audio(chunk, is_final=is_final)
        except Exception as e:
            logging.error(f"ASR 处理失败: {e}")

    async def handle_ws(self, websocket, components):
        """
        这里主要是接收数据
        """
        await websocket.accept()  # 必须先接受连接
        logging.info("WebSocket 连接已接受")
        
        # 初始化导演
        self.director = Director(components)

        # 初始化角色 (此时可传入剧本引用)
        self.init_characters(components)
        logging.info(f"已加载角色: {list(self.characters.keys())}")

        # 启动演出编排器后台任务 (现在由导演驱动)
        self.orchestrator_task = asyncio.create_task(self.director.run_orchestrator(websocket, self.characters))

        try:
            # 主循环：接收消息并处理
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                
                # 统一验证 token
                if not self._validate_token(msg):
                    logging.warning(f"接收到未授权的消息")
                    await websocket.send_text(json.dumps({"type": "error", "message": "无效的 token"}))
                    continue
                
                msg_type = msg.get("type")

                if msg_type == "chat":
                    user_text = msg.get("data")
                    await self._dispatch_chat(user_text)
                
                elif msg_type == "audio":
                    await self._handle_audio(components, msg)
                
                elif msg_type == "interrupt":
                    await self.interrupt_chat(websocket)

        except WebSocketDisconnect:
            logging.info("WebSocket 已断开")
        except Exception as e:
            logging.error(f"WebSocket 异常: {e}")
        finally:
            # 停止编排器
            if self.orchestrator_task:
                self.orchestrator_task.cancel()
            
            # 停止所有角色的内部后台任务
            for char in self.characters.values():
                await char.stop_tasks()
