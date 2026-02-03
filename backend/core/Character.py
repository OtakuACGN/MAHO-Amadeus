import asyncio
import logging
import re
import base64


class Character:
    """
    一个纯粹的处理器，当我调用chat函数之后，
    会在自身的输出队列出现一个有着开头，然后中间是各种音频或者文字片段，然后结尾是一个结束的这种队列。
    """

    def __init__(self, name: str, config: dict, components=None):
        self.name = name
        self.components = components

        self.system_prompt = config.get("system_prompt", "")
        # 存储该角色特定的 TTS 配置（如参考音频路径、提示词等）
        self.tts_config = config.get("tts_config", {})

        self.history = []
        if self.system_prompt:
            self.history.append(
                {"role": "system", "content": self.system_prompt})

        self.message_queue = asyncio.Queue()  # LLM 原始输出队列
        self.sentence_queue = asyncio.Queue()  # TTS 句子队列
        self.output_queue = asyncio.Queue()   # 处理完毕后的结果输出队列 (供外部消费)

        self.tasks = []
        if self.components:
            self.start_tasks()
            # 注册 TTS 角色
            self._register_tts_character()
            
    def _register_tts_character(self):
        """注册 TTS 角色信息"""
        if not self.components or not hasattr(self.components.tts, 'register_character'):
            return
        
        char_name = self.tts_config.get("character_name", self.name)
        model_dir = self.tts_config.get("onnx_model_dir")
        if char_name and model_dir:
            try:
                self.components.tts.register_character(char_name, model_dir)
                logging.info(f"[{self.name}] TTS 角色 '{char_name}' 已注册")
            except Exception as e:
                logging.error(f"[{self.name}] 注册 TTS 角色失败: {e}")

    def start_tasks(self):
        """启动后台处理任务"""
        self.tasks = [
            asyncio.create_task(self._process_char_loop()),
            asyncio.create_task(self._process_audio_loop())
        ]

    async def stop_tasks(self):
        """停止后台任务"""
        for task in self.tasks:
            if task and not task.done():
                task.cancel()
        if self.tasks:
            try:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            except Exception:
                pass
        self.tasks = []

    async def interrupt(self):
        """中断当前处理逻辑并清空队列"""
        # 1. 清空输入队列
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except asyncio.QueueEmpty:
                break

        while not self.sentence_queue.empty():
            try:
                self.sentence_queue.get_nowait()
                self.sentence_queue.task_done()
            except asyncio.QueueEmpty:
                break

        # 2. 向输出队列发送一个中断/清理信号（可选）
        # 这里暂时只清空
        logging.info(f"[{self.name}] 已中断当前处理并清空队列")

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

    async def chat(self, user_text: str):
        """
        触发角色的推理流程。
        结果会推入 output_queue 中。
        """
        if not self.components:
            logging.error(f"[{self.name}] 无法开启对话：未绑定 Components")
            return

        # 提前申请 TTS 资源锁
        await self.components.tts_lock.reserve(self.name)

        # 投递开始信号
        await self.output_queue.put({"type": "start", "character": self.name})
        logging.info(f"[{self.name}] 成功收到并开始处理: {user_text}")

        # 添加用户历史
        self.add_history_user(user_text)

        full_response = ""
        # 流式调用 LLM
        async for response in self.components.llm.generate(self.history):
            full_response += response
            await self.message_queue.put(response)

        # 更新助手历史
        self.add_history_assistant(full_response)

        # 等待后台处理队列全部完成（消费完毕）
        await self.message_queue.join()
        await self.sentence_queue.join()

        # 投递结束信号
        await self.output_queue.put({"type": "end", "character": self.name})

        # 释放TTS资源锁
        await self.components.tts_lock.release(self.name)
        logging.info(f"[{self.name}] 对话推理与后处理已全部完成")

    async def _process_char_loop(self):
        """
        后台处理循环：处理字符队列 -> 过滤 -> 投递到 output_queue -> 组合句子发送至音频队列
        """
        buffer = ""
        is_thinking = False
        sentence_endings = re.compile(r'[。！？.!?\n]+')

        while True:
            try:
                char = await self.message_queue.get()

                # 思维链标签处理
                if "<think>" in char:
                    is_thinking = True
                    char = char.replace("<think>", "")
                if "</think>" in char:
                    is_thinking = False
                    char = char.replace("</think>", "")

                # 筛选杂质字符（保留正常标点和空格）
                unwanted_chars = ["\n", "\t", "\r"]
                if not char or char in unwanted_chars:
                    self.message_queue.task_done()
                    continue

                # 投递文本片段到外部输出队列
                msg_type = "thinkText" if is_thinking else "text"
                await self.output_queue.put({
                    "type": msg_type,
                    "data": char,
                    "character": self.name
                })

                # 非思考模式下进行断句
                if not is_thinking:
                    buffer += char
                    if sentence_endings.search(char):
                        sentence = buffer.strip()
                        if sentence:
                            await self.sentence_queue.put(sentence)
                        buffer = ""

                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[{self.name}] 字符处理循环异常: {e!r}")

    async def _process_audio_loop(self):
        """
        后台处理循环：处理句子队列 -> 翻译 -> TTS -> 投递音频分片到 output_queue
        """
        while True:
            try:
                sentence = await self.sentence_queue.get()
                loop = asyncio.get_event_loop()

                # 1. 翻译成日语
                ja_sentence = await loop.run_in_executor(None, self.components.translator.translate, sentence)

                # 2. 获取 TTS 资源锁
                await self.components.tts_lock.acquire(self.name)
                try:
                    # 调用 TTS 生成音频
                    audio_data = await loop.run_in_executor(
                        None,
                        lambda: self.components.tts.generate_audio(
                            ja_sentence, **self.tts_config)
                    )
                finally:
                    pass

                # 3. 如果有音频，分片投递到输出队列
                if audio_data:
                    CHUNK_SIZE = 30 * 1024
                    total_len = len(audio_data)
                    for i in range(0, total_len, CHUNK_SIZE):
                        chunk_data = audio_data[i:i + CHUNK_SIZE]
                        chunk_b64 = base64.b64encode(chunk_data).decode()
                        await self.output_queue.put({
                            "type": "audio",
                            "data": chunk_b64,
                            "is_final": (i + CHUNK_SIZE >= total_len),
                            "character": self.name
                        })

                self.sentence_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[{self.name}] 音频处理循环异常: {e!r}")
