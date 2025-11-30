import asyncio
import websockets
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import io

async def test_ws():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("已连接到服务器，输入内容并回车发送，直接回车退出。")
        import json, base64
        while True:
            msg = input("输入: ")
            if not msg:
                print("已退出。"); break
            await websocket.send(msg)
            try:
                receiving = False
                audio_chunks = []  # 每次会话初始化音频分片缓冲区
                while True:
                    response = await websocket.recv()
                    try:
                        obj = json.loads(response)
                        if obj.get("type") == "start":
                            print("---开始接收---")
                            receiving = True
                            continue
                        elif obj.get("type") == "end":
                            print("---接收结束---")
                            break
                        elif obj.get("type") == "text" and receiving:
                            print("收到字符:", obj["data"])
                        elif obj.get("type") == "audio" and receiving:
                            # 只处理 base64 音频分片
                            audio_chunks.append(obj["data"])
                            if obj.get("is_final", False):
                                try:
                                    audio_bytes = base64.b64decode("".join(audio_chunks))
                                    rate, data = wavfile.read(io.BytesIO(audio_bytes))
                                    if data.dtype != np.float32:
                                        data = data.astype(np.float32) / np.iinfo(data.dtype).max
                                    sd.play(data, rate)
                                    sd.wait()
                                except Exception as e:
                                    print(f"音频播放失败: {e}")
                                audio_chunks = []
                            else:
                                print(f"收到音频分片，长度: {len(obj['data'])}")
                        else:
                            print("收到未知类型:", obj)
                    except Exception:
                        print("收到原始内容:", response)
            except Exception as e:
                print(f"接收失败: {e}"); break

asyncio.run(test_ws())