import os
import logging
import tempfile
from pathlib import Path


class Client:
    """
    Genie TTS 客户端 - 简化版，仅保留注册和生成功能
    """
    
    def __init__(self, 
                 genie_data_dir: str = "", 
                 language: str = "ja", 
                 onnx_model_dir: str = "",
                 **kwargs):
        # 获取项目根目录 (MAHO)
        self.project_root = Path(__file__).resolve().parents[4]
        self.default_lang = language
        
        # 处理 GenieData 目录路径
        if not genie_data_dir:
            # 默认路径：backend/models/GenieData
            genie_data_dir = str(self.project_root / "backend" / "models" / "GenieData")
        elif not Path(genie_data_dir).is_absolute():
            genie_data_dir = str(self.project_root / genie_data_dir)
        
        # 设置 GENIE_DATA_DIR 环境变量（必须在导入 genie_tts 之前）
        os.environ["GENIE_DATA_DIR"] = genie_data_dir
        logging.info(f"GENIE_DATA_DIR 已设置为: {genie_data_dir}")
        
        # 导入 genie_tts
        import genie_tts as genie
        self.genie = genie

        # 如果配置中有默认模型目录，先注册一个默认角色 'maho'
        if onnx_model_dir:
            self.register_character("maho", onnx_model_dir)

    def register_character(self, char_name: str, model_dir: str, language: str = None):
        """
        在 Genie 中加载/注册一个人物
        """
        # 处理模型路径
        path_obj = Path(model_dir)
        if not path_obj.is_absolute():
            path_obj = self.project_root / model_dir
        
        real_model_dir = str(path_obj)
        lang = language or self.default_lang
        
        logging.info(f"正在注册角色: {char_name}, 模型路径: {real_model_dir}, 语言: {lang}")
        self.genie.load_character(
            character_name=char_name,
            onnx_model_dir=real_model_dir,
            language=lang
        )

    def generate_audio(self, text: str, character_name: str = None, reference_audio_path: str = None, reference_audio_text: str = None, **kwargs) -> bytes | None:
        """
        根据已注册的人物名称生成音频
        """
        # 获取角色名，默认使用 'maho'
        char_name = character_name or "maho"
        
        try:
            # 如果提供了参考音频，则设置参考音频
            if reference_audio_path and reference_audio_text:
                # 处理音频路径
                ref_path = Path(reference_audio_path)
                if not ref_path.is_absolute():
                    ref_path = self.project_root / reference_audio_path
                
                self.genie.set_reference_audio(
                    character_name=char_name,
                    audio_path=str(ref_path),
                    audio_text=reference_audio_text,
                )
                logging.info(f"参考音频已设置 ({char_name}): {ref_path}")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # 使用 genie.tts 生成音频
                self.genie.tts(
                    character_name=char_name,
                    text=text,
                    play=False,
                    save_path=tmp_path
                )
                
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()
                return audio_data
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logging.error(f"TTS 生成失败 ({char_name}): {e}")
            return None
