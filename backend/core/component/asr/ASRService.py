import importlib
import asyncio


class ASR:
    """
    ASR 服务类 (中转层)
    
    该类负责加载具体的 ASR 实现 (Provider)，并将调用透传。
    
    【Provider 接口规范】
    任何接入的 ASR 模块 (如 xfyun_asr) 需实现以下方法:
    
    1. async def start(self): 
       - (可选) 初始化资源，通常在首次 send_audio 时自动调用
       
    2. async def send_audio(self, chunk: bytes, is_final: bool = False):
       - 处理音频发送逻辑。
       - chunk: 音频数据的字节流
       - is_final: 是否为本次语音的最后一帧。如果是，Provider 应发送结束信号。
       
    3. def get_result(self) -> str:
       - 返回当前缓冲区内的识别文本，并清空缓冲区。
    
    """
    def __init__(self, config: dict) -> None:
        # 获取配置中的模块名
        select = config.get("select", "volcengine_api")
        
        # 如果是 none，不加载任何 provider
        if select == "none":
            self.provider = None
            return

        # 动态导入模块
        try:
            module = importlib.import_module(
                f".{select}", package="core.component.asr")
        except ImportError as e:
            raise ImportError(f"无法加载模块 {select}: {e}")

        # 获取对应的类
        client_class = getattr(module, "Client", None)
        if not client_class:
            raise ValueError(f"在模块 {select} 中找不到名为 'Client' 的类")

        # 实例化 Provider
        asr_config = config.get(select, {})
        self.provider = client_class(**asr_config)

    async def start(self):
        """
        启动 ASR 会话 (兼容接口)
        具体的连接管理由 Provider 在 send_audio 时根据需要自行处理
        """
        if self.provider and hasattr(self.provider, 'start'):
            await self.provider.start()

    async def send_audio(self, chunk: bytes, is_final: bool = False):
        """
        发送音频数据
        :param chunk: 音频数据的字节流
        :param is_final: 是否为这一句话的结束
        """
        if self.provider:
            await self.provider.send_audio(chunk, is_final=is_final)

    def get_result(self) -> str:
        """
        从 Provider 获取并清空当前的识别结果
        """
        if self.provider and hasattr(self.provider, 'get_result'):
            return self.provider.get_result()
        return "" 

