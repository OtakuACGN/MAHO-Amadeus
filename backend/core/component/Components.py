from pathlib import Path
import asyncio
from core.util.config import load_yaml
from core.component.llm.LLMService import LLM
from core.component.tts.TTSService import TTS
from core.component.translator.TranslatorService import Translator
from core.component.asr.ASRService import ASR
from core.util.resource_lock import ResourceLock


class Components:
    """
        Components核心类，负责初始化和管理核心功能
    """

    def __init__(self):
        config_path = Path("config.yaml")
        self.config = load_yaml(config_path)
        
        # 读取 components 下的组件配置
        components_config = self.config.get("components", {})
        
        self.llm = LLM(components_config.get("llm", {}))
        self.tts = TTS(components_config.get("tts", {}))
        self.translator = Translator(components_config.get("translator", {}))
        self.asr = ASR(components_config.get("asr", {}))

        self.tts_lock = ResourceLock()  # TTS 独占资源锁