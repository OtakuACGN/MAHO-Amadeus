import asyncio
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websockets

class Client:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        
        # 回调函数
        self.callback = None
        
        # 状态 0: first, 1: continue, 2: last
        self.status = 0
        self.text_buffer = ""

    def set_callback(self, callback):
        """设置回调函数"""
        self.callback = callback

    def create_url(self):
        url = 'wss://iat.cn-huabei-1.xf-yun.com/v1'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + "iat.cn-huabei-1.xf-yun.com" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v1 " + "HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": "iat.cn-huabei-1.xf-yun.com"
        }
        return url + '?' + urlencode(v)

    async def start(self):
        """建立 ASR 连接 (通常由 send_audio 懒加载调用)"""
        if self.ws:
            return

        ws_url = self.create_url()
        try:
            self.ws = await websockets.connect(ws_url)
            self.status = 0
            self.text_buffer = ""
            asyncio.create_task(self._listen())
            logging.info("ASR (Xfyun) 连接已建立")
        except Exception as e:
            logging.error(f"ASR 连接失败: {e}")
            self.ws = None

    async def _listen(self):
        """监听 ASR 返回结果并写入 buffer"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                code = data["header"]["code"]
                if code != 0:
                    logging.error(f"ASR Error: {code} - {data['header'].get('message', '')}")
                    await self.close()
                    break
                
                payload = data.get("payload")
                if payload:
                    result_text = payload["result"]["text"]
                    result_json = json.loads(base64.b64decode(result_text).decode('utf-8'))
                    
                    partial_text = ""
                    for i in result_json['ws']:
                        for j in i["cw"]:
                            partial_text += j["w"]
                    
                    if partial_text:
                        self.text_buffer += partial_text
                
                if data["header"]["status"] == 2:
                    logging.info(f"ASR 会话结束 (Remote), 结果: {self.text_buffer}")
                    
                    # 收到服务端结束信号，触发回调
                    if self.text_buffer and self.callback:
                        # 异步执行回调，只传递文本结果
                        asyncio.create_task(self.callback(self.text_buffer))

                    # 服务端确认结束，关闭连接
                    await self.close()
                    break
        except Exception as e:
            # 正常关闭或网络波动
            pass
        finally:
            await self.close()

    async def close(self):
        """关闭连接并清理"""
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
            self.status = 0

    async def send_audio(self, chunk, is_final=False):
        """
        发送音频分片
        :param chunk: 音频数据
        :param is_final: 是否是最后一帧
        """
        if not self.ws:
            await self.start()
            if not self.ws:
                return # 连接失败直接返回

        # 1. 发送数据 (如果有)
        if chunk:
            audio_b64 = base64.b64encode(chunk).decode('utf-8')
            
            data = {}
            if self.status == 0:
                # 第一帧
                data = {
                    "header": {"status": 0, "app_id": self.app_id},
                    "parameter": {
                        "iat": {
                            "domain": "slm", "language": "mul_cn", "accent": "mandarin",
                            "result": {"encoding": "utf8", "compress": "raw", "format": "json"}
                        }
                    },
                    "payload": {"audio": {"audio": audio_b64, "sample_rate": 16000, "encoding": "raw"}}
                }
                self.status = 1
            else:
                # 中间帧
                data = {
                    "header": {"status": 1, "app_id": self.app_id},
                    "payload": {"audio": {"audio": audio_b64, "sample_rate": 16000, "encoding": "raw"}}
                }
                
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                logging.error(f"ASR 发送音频失败: {e}")
                await self.close()
                return

        # 2. 如果是最后一帧，发送结束包 (status=2, empty audio)
        if is_final:
            data_end = {
                "header": {"status": 2, "app_id": self.app_id},
                "payload": {"audio": {"audio": "", "sample_rate": 16000, "encoding": "raw"}}
            }
            try:
                await self.ws.send(json.dumps(data_end))
            except Exception as e:
                logging.error(f"ASR 发送结束包失败: {e}")
                await self.close()