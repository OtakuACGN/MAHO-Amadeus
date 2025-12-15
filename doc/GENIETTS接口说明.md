# Genie TTS 组件使用说明

## 简介

Genie TTS 是一个轻量化的 TTS（文本转语音）推理服务，使用 ONNX 模型进行语音合成。相比传统方法，模型体积减小数十倍，推理速度更快。
<br>
感谢 [Genie-tts](https://github.com/High-Logic/Genie-TTS)。

## 文件部署
[首先点击我在这个链接下载好需要的文件](https://www.modelscope.cn/models/bysq2006/maho-tts2/files)
maho2-e15.ckpt
maho2_e8_s528.pth
这两个是训练用的模型文件
GenieData.zip
这个是项目依赖项，是一个目录。
TTS-maho.zip
这个是ONNX模型文件，是一个目录。

### 1. 复制模型文件

将以下目录复制到 `backend/models/` 下：

- `TTS-maho/` → `backend/models/TTS-maho/`
- `GenieData/` → `backend/models/GenieData/`

### 2. 安装依赖
如果你已经在后端执行过下载所有依赖的话，就不用。
```bash
pip install genie-tts
```

### 3. 更新配置

修改 `backend/config.yaml`，设置 `tts的select为genie_tts_service`

### 4. 启动服务

```bash
cd backend
python main.py
```

## 配置方法

在 `backend/config.yaml` 中添加或修改 TTS 配置：

```yaml
tts:
  select: genie_tts_service  # 可选: gpt_sovits_api 或 genie_tts_service
  # Genie TTS 配置（轻量化 ONNX 推理）
  genie_tts_service:
    character_name: "maho" # 随便起什么名字都行，主要是为了区分不同角色
    onnx_model_dir: "backend/models/TTS-maho"
    genie_data_dir: "backend/models/GenieData"
    language: "ja"                            # ja/zh/en
    reference_audio_path: "Modeltmp/TTS/WAV-MAHO/vocal_00_02_MAH0002.wav.reformatted.wav_10.wav_0000000000_0000171840.wav"
    reference_audio_text: "そんなのわかっているわ。何度同じ話を繰り返せば気が済むの?"
    auto_load: true
  # GPT-SoVITS 配置（原有配置）
  gpt_sovits_api:
    base_url: "http://127.0.0.1:9880"
    refer_wav_path: "C:\\Users\\19045\\Desktop\\MAHO\\backend\\data\\TTS-audio\\激动.wav"
    prompt_text: "あら、あなた。"
    prompt_language: "ja"
    default_text_language: "ja"
    speed: 1.2
```

## 配置说明

### 必需参数

- `character_name`: 角色名称，用于标识不同的语音模型
- `onnx_model_dir`: ONNX 模型文件所在目录
- `genie_data_dir`: GenieData 依赖项目录

### 可选参数

- `language`: 语言代码，默认 "ja"（日语）
  - `ja`: 日语
  - `zh`: 中文
  - `en`: 英语
  
- `reference_audio_path`: 参考音频文件路径，用于情感和语调克隆
- `reference_audio_text`: 参考音频对应的文本内容
- `auto_load`: 是否在初始化时自动加载模型，默认 `true`


## 优势

1. **轻量化**: ONNX 模型体积比原始模型小数十倍
2. **快速推理**: 优化的 ONNX 推理引擎，速度更快
3. **易于部署**: 不需要 GPU，CPU 即可高效运行
4. **兼容性强**: 与现有 TTS 服务架构完全兼容