import logging

class Client:
    """
    None ASR Client: 不执行任何操作的 ASR 占位组件。
    """
    def __init__(self, **kwargs):
        logging.info("ASR 已设置为 'none'，将不处理音频输入。")

    async def start(self, on_result_callback):
        """启动 ASR (不执行任何操作)"""
        pass

    async def send_audio(self, chunk):
        """发送音频分片 (不执行任何操作)"""
        pass

    async def finish_audio(self):
        """发送结束帧 (不执行任何操作)"""
        pass
