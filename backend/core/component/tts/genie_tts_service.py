import os
import logging
import io
import threading
from pathlib import Path


class Client:
    """
    Genie TTS 客户端 - 轻量化的 TTS 推理服务
    使用 ONNX 模型进行语音合成
    """
    
    def __init__(self,
                 character_name: str = "maho",
                 onnx_model_dir: str = "",
                 genie_data_dir: str = "",
                 language: str = "ja",
                 reference_audio_path: str = "",
                 reference_audio_text: str = "",
                 auto_load: bool = True):
        """
        初始化 Genie TTS 客户端
        虽然看起来非常长，但是实际上它只干了配置本身的各种字符串和导入Genie-TTS库这几件事。
        
        :param character_name: 角色名称
        :param onnx_model_dir: ONNX 模型目录路径（相对或绝对路径）
        :param genie_data_dir: GenieData 依赖项目录路径（相对或绝对路径）
        :param language: 语言代码（ja/zh/en）
        :param reference_audio_path: 参考音频路径
        :param reference_audio_text: 参考音频对应的文本
        :param auto_load: 是否自动加载模型
        """
        self.lock = threading.Lock()
        self.loaded_characters = set()
        
        self.character_name = character_name
        self.language = language
        self.reference_audio_path = reference_audio_path
        self.reference_audio_text = reference_audio_text
        self.is_loaded = False
        
        # 获取项目根目录（MAHO 目录）
        # __file__ = backend/core/component/tts/genie_tts_service.py
        # parents: 0=tts, 1=component, 2=core, 3=backend, 4=MAHO
        project_root = Path(__file__).resolve().parents[4]
        self.project_root = project_root
        
        # 处理 ONNX 模型目录路径
        if onnx_model_dir:
            model_path = Path(onnx_model_dir)
            if not model_path.is_absolute():
                model_path = project_root / onnx_model_dir
            self.onnx_model_dir = str(model_path)
        else:
            # 默认路径：backend/models/TTS-maho
            self.onnx_model_dir = str(project_root / "backend" / "models" / "TTS-maho")
        
        # 处理 GenieData 目录路径
        if genie_data_dir:
            genie_path = Path(genie_data_dir)
            if not genie_path.is_absolute():
                genie_path = project_root / genie_data_dir
            genie_data_dir = str(genie_path)
        else:
            # 默认路径：backend/models/GenieData
            genie_data_dir = str(project_root / "backend" / "models" / "GenieData")
        
        # 设置 GENIE_DATA_DIR 环境变量（必须在导入 genie_tts 之前）
        os.environ["GENIE_DATA_DIR"] = genie_data_dir
        logging.info(f"GENIE_DATA_DIR 已设置为: {genie_data_dir}")
        
        # 导入 genie_tts（在设置环境变量之后）
        import genie_tts as genie
        self.genie = genie
        
        # 如果启用自动加载，则初始化模型
        if auto_load:
            self._load_model()
    
    def _ensure_character_loaded(self, character_name: str, model_dir: str):
        """确保指定角色已加载"""
        if character_name in self.loaded_characters:
            return

        with self.lock:
            # 双重检查
            if character_name in self.loaded_characters:
                return
                
            try:
                # 处理模型路径
                path_obj = Path(model_dir)
                if not path_obj.is_absolute():
                     path_obj = self.project_root / model_dir
                
                real_model_dir = str(path_obj)
                
                logging.info(f"正在加载角色: {character_name}, 模型路径: {real_model_dir}")
                self.genie.load_character(
                    character_name=character_name,
                    onnx_model_dir=real_model_dir,
                    language=self.language,
                )
                self.loaded_characters.add(character_name)
                logging.info(f"成功加载角色: {character_name}")
            except Exception as e:
                logging.error(f"加载角色 {character_name} 失败: {e}")
                raise

    def _load_model(self):
        """加载默认 Genie TTS 模型"""
        self._ensure_character_loaded(self.character_name, self.onnx_model_dir)
            
        # 如果提供了参考音频，则设置参考音频
        if self.reference_audio_path and self.reference_audio_text:
            self._set_reference_audio(
                self.reference_audio_path, 
                self.reference_audio_text,
                character_name=self.character_name
            )
        
        self.is_loaded = True
    
    def _set_reference_audio(self, audio_path: str, audio_text: str, character_name: str = None):
        """设置参考音频"""
        target_char = character_name or self.character_name
        try:
            # 处理音频路径
            ref_path = Path(audio_path)
            if not ref_path.is_absolute():
                # 使用项目根目录作为基准
                ref_path = self.project_root / audio_path
            
            with self.lock:
                self.genie.set_reference_audio(
                    character_name=target_char,
                    audio_path=str(ref_path),
                    audio_text=audio_text,
                )
            logging.info(f"参考音频已设置 ({target_char}): {ref_path}")
            
        except Exception as e:
            logging.error(f"设置参考音频失败: {e}")
            raise
    
    def generate_audio(self, 
                      text: str, 
                      reference_audio_path: str = None,
                      reference_audio_text: str = None,
                      **kwargs) -> bytes | None:
        """
        生成音频数据
        
        :param text: 要合成的文本
        :param reference_audio_path: 临时参考音频路径（可选）
        :param reference_audio_text: 临时参考音频文本（可选）
        :param kwargs: 可选参数，包括 character_name, onnx_model_dir
        :return: 音频二进制数据（WAV 格式）
        """
        # 提取动态参数
        target_char = kwargs.get("character_name", self.character_name)
        # 如果是新角色，尝试从 kwargs 获取模型目录，否则用默认目录（可能不正确，但在配置完善的情况下应该总是有）
        target_model_dir = kwargs.get("onnx_model_dir", self.onnx_model_dir)

        # 确保角色已加载
        if not self.is_loaded and target_char == self.character_name:
             logging.error("默认模型未加载且未指定新角色信息。")
             return None
        
        try:
            self._ensure_character_loaded(target_char, target_model_dir)

            # 如果提供了临时参考音频，则更新参考音频
            if reference_audio_path and reference_audio_text:
                self._set_reference_audio(reference_audio_path, reference_audio_text, character_name=target_char)
            
            # 生成音频到内存
            audio_buffer = io.BytesIO()
            
            # 使用 genie.tts 生成音频
            # 注意: genie_tts 默认保存到文件，我们需要生成临时文件然后读取
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # 生成音频 - 加锁保护
                with self.lock:
                    self.genie.tts(
                        character_name=target_char,
                        text=text,
                        play=False,  # 不播放
                        save_path=tmp_path,
                    )
                
                # 读取生成的音频文件
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()
                
                logging.info(f"成功为文本生成音频 ({target_char}): {text[:50]}...")
                return audio_data
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logging.error(f"TTS 生成失败 ({target_char}): {e}")
            return None
    
    def set_reference(self, audio_path: str, audio_text: str):
        """
        更新参考音频
        
        :param audio_path: 参考音频路径
        :param audio_text: 参考音频对应的文本
        """
        self.reference_audio_path = audio_path
        self.reference_audio_text = audio_text
        if self.is_loaded:
            self._set_reference_audio(audio_path, audio_text)
