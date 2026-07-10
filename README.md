# z-audio-study-webpage-qwen

把一段本地音频（课堂录音、播客、讲座、会议、访谈）做成**可复习的学习网页**。

- 音频先转写成带时间戳的文本（Whisper 本地 / DashScope paraformer 云端 / 直接喂现成转写）
- 再用 Qwen 文本模型按时间切段理解
- 生成图文并茂的 HTML 学习网页：**每个关键知识点都绑定一个可点击时间戳**，点一下就从音频那个位置播放

对应视频版技能：`z-video-study-webpage-qwen`（本技能是它的音频孪生版，去掉抽帧与多模态，改为知识点绑定时间戳）。

## 安装

把整个文件夹放进你的技能目录即可被 WorkBuddy 自动发现：

```bash
# Windows
copy 文件夹 z-audio-study-webpage-qwen 到 %USERPROFILE%\.workbuddy\skills\

# macOS / Linux
cp -r z-audio-study-webpage-qwen ~/.workbuddy/skills/
```

依赖：Python 3.11+、 `requests`、ffmpeg/ffprobe（系统 PATH）。本地转写后端三选一：

- **Vosk（推荐，纯本地、不依赖 torch / 云端权限）**：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple vosk soundfile`，再从 https://alphacephei.com/vosk/models 下载中文小模型 `vosk-model-small-cn-0.22`（zip，约 42MB）解压，运行加 `--vosk-model <模型目录>`。
- Whisper 本地：`pip install faster-whisper` 或 `openai-whisper`（注意：本机实测 ctranslate2 段错误 + torch DLL 被安全软件拦截，两种 whisper 都跑不起来，建议直接用 Vosk）。
- DashScope 云端 paraformer：`--asr dashscope`，需该 key 已开通「文件转写」服务权限（免费 key 通常额度不足，走不通）。

> **关于 DashScope 的重要提醒**：`--asr dashscope` 需要该 key 已开通 DashScope「文件转写」服务权限与额度；Qwen-Audio 免费额度也易耗尽（`403 Free allocated quota exceeded`）。所以**云端 ASR 在免费 key 上基本不可用**，本地 Vosk 是唯一出路。Qwen **文本分析**（qwen3.7-plus 对话端点）只需普通对话 key 即可，不受影响。

## 朋友拿到后怎么用（3 步）

本技能**零配置就能跑**：本地 Vosk 转写 + Qwen 文本分析，不用手动下模型、不用选后端。

1. **解压文件夹，整个丢进自己的 `~/.workbuddy/skills/`**
   - Windows：`%USERPROFILE%\.workbuddy\skills\z-audio-study-webpage-qwen`
   - macOS / Linux：`~/.workbuddy/skills/z-audio-study-webpage-qwen`
2. **一键装依赖 + 预热 Vosk 模型**
   ```bash
   python scripts/setup.py        # Windows 用 python；macOS/Linux 用 python3
   ```
   （用清华镜像装依赖，并自动下载中文小模型 `vosk-model-small-cn-0.22` 到 `~/.cache/vosk-models/`）
3. **把音频转成学习网页**（默认 `--asr auto`，自动用 Vosk 本地转写）
   ```bash
   python audio_study.py --audio 音频.mp3 --title 主题
   ```

> 默认 `--asr auto`（Vosk → Whisper → DashScope 兜底），朋友**不用关心后端和模型路径**，给音频就出网页。

**唯一需要朋友自己准备的**：一个能调 Qwen 文本对话的 `DASHSCOPE_API_KEY`（设成环境变量即可，**不写进文件**）。

- 怎么拿这个 Key？看仓库里的 **`通义千问 API.docx`**：阿里云百炼控制台 → API-KEY 管理 → 创建 API-KEY → 复制 `sk-` 开头的密钥 → 设到环境变量 `DASHSCOPE_API_KEY`。
- 本技能只用 Qwen **文本对话**端点（`qwen3.7-plus`），普通对话 key 即可；云端 ASR / Qwen-Audio 额度问题不影响文本分析。

## 四种使用方式

```bash
# 0) 设置密钥（仅当前会话，不要写进文件）
export DASHSCOPE_API_KEY="你的key"

# A) 云端 ASR 自动转写 + Qwen 分析（需 key 已开通文件转写权限）
python3 scripts/audio_study.py --audio lecture.mp3 --title "课程主题" --asr dashscope

# B) 本地 Whisper 转写（本机可能跑不起来，见上）
python3 scripts/audio_study.py --audio lecture.mp3 --title "课程主题" --asr whisper

# B2) 本地 Vosk 离线转写（本机首选，零云端依赖）
python3 scripts/audio_study.py --audio lecture.mp3 --title "课程主题" \
  --asr vosk --vosk-model /path/to/vosk-model-small-cn-0.22

# C) 已有转写文本，直接分析
python3 scripts/audio_study.py --audio lecture.mp3 --transcript transcript.txt --title "课程主题"
```

只验证网页模板（无需密钥、无需转写）：

```bash
python3 scripts/audio_study.py --audio lecture.mp3 --title "课程主题" --mock-analysis
```

## 输出

```text
study-audio/
├── study-summary-audio.html   # 最终学习网页（本地音频可播放 + 时间戳跳转）
├── qwen-analysis.json
├── qwen-segments.json
├── transcript.txt / transcript.json
└── run-report.json
```

## 安全

API Key 只从环境变量 `DASHSCOPE_API_KEY` 读取，不会写入任何输出文件。

## License

MIT
