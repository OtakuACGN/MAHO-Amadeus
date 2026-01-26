import logging
import asyncio
import re
import json
import base64

async def handle_chat(websocket, manager, character, user_text):
    """
    聊天处理逻辑
    """
    # 发送开始标签
    await websocket.send_text(json.dumps({"type": "start", "character": character.name}))
    logging.info(f"[{character.name}] 成功收到: {user_text}")

    # 更新用户上下文
    character.add_history_user(user_text)

    full_response = ""
    # 注意：这里假设 manager.llm.generate 每一块 yield 的都是字符串
    async for response in manager.llm.generate(character.history):
        full_response += response
        await character.message_queue.put(response)

    # 更新助手上下文
    character.add_history_assistant(full_response)

    # 等待两个队列都处理完毕
    await character.message_queue.join()
    await character.sentence_queue.join()

    # 发送结束标签
    await websocket.send_text(json.dumps({"type": "end", "character": character.name}))

async def process_char_queue(manager, character, websocket):
    """
    处理字符队列：发送字符流 -> 组合成句子 -> 放入句子队列
    """
    buffer = ""
    is_thinking = False
    # 定义结束标点符号，用于断句
    sentence_endings = re.compile(r'[。！？.!?\n]+')

    while True:
        try:
            char = await character.message_queue.get()

            if "<think>" in char:
                is_thinking = True
                char = char.replace("<think>", "")
            if "</think>" in char:
                is_thinking = False
                char = char.replace("</think>", "")

            # 筛选掉没用的字符
            unwanted_chars = ["\n", "\t", " ", "\r"]
            if not char or char.strip() == "" or char in unwanted_chars:
                character.message_queue.task_done()
                continue

            # 发送字符流（带标签）
            msg_type = "thinkText" if is_thinking else "text"
            await websocket.send_text(json.dumps({
                "type": msg_type, 
                "data": char,
                "character": character.name
            }))

            if not is_thinking:
                buffer += char

                # 检查是否形成完整句子
                if sentence_endings.search(char):
                    sentence = buffer.strip()
                    if sentence:
                        # 将完整句子放入句子队列，供 TTS 处理
                        await character.sentence_queue.put(sentence)
                    buffer = ""  # 清空缓冲区

            character.message_queue.task_done()

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"[{character.name}] 字符队列处理出错: {e!r}")

async def process_sentence_queue(manager, character, websocket):
    """
    处理句子队列：翻译 -> TTS -> 发送音频流
    """
    while True:
        try:
            sentence = await character.sentence_queue.get()

            loop = asyncio.get_event_loop()
            # 翻译成日语
            ja_sentence = await loop.run_in_executor(None, manager.translator.translate, sentence)
            logging.info(f"[{character.name}] 翻译结果: {ja_sentence}")

            # 调用 TTS 生成音频 (在线程池中运行以避免阻塞)
            # 使用 character.tts_config 作为动态参数传入
            audio_data = await loop.run_in_executor(
                None, 
                lambda: manager.tts.generate_audio(ja_sentence, **character.tts_config)
            )
            
            if audio_data:
                # 分片发送音频，避免超过 WebSocket 消息大小限制
                CHUNK_SIZE = 30 * 1024  # 30KB, 是 3 的倍数
                total_len = len(audio_data)

                for i in range(0, total_len, CHUNK_SIZE):
                    chunk_data = audio_data[i:i + CHUNK_SIZE]
                    chunk_b64 = base64.b64encode(chunk_data).decode()
                    await websocket.send_text(json.dumps({
                        "type": "audio",
                        "data": chunk_b64,
                        "is_final": (i + CHUNK_SIZE >= total_len),
                        "character": character.name
                    }))

                logging.info(f"[{character.name}] 已分片发送音频数据，总长度: {total_len}")
            else:
                logging.warning(f"[{character.name}] TTS 生成失败")

            character.sentence_queue.task_done()

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"[{character.name}] 句子队列处理出错: {e!r}")
