---
name: z-audio-study-webpage-qwen
description: 当用户要求"把音频做成学习网页""音频转学习笔记""理解这段录音/播客/课程""音频学习总结网页""用 Qwen 分析音频内容""把录音转成可复习资料"时必须使用。本 skill 会把本地音频（mp3/wav/m4a 等）转写成带时间戳的文本，用 DashScope OpenAI-compatible API 的 qwen 文本模型逐段分析，并生成图文并茂（知识点绑定可点击时间戳）的 HTML 学习网页。与 z-video-study-webpage-qwen 对应，但处理纯音频、无需画面。
---

# Qwen 音频学习网页

把一段音频真正拆开学习：先转写成带时间戳的文本，再让 Qwen 按时间切段理解，最后生成学习总结网页。网页沿用 `study-summary` 的视觉模板：米色纸张、卡片、时间线、本地音频播放器、**关键知识点 × 可点击时间戳**（点了直接从该位置播放）。

> 与 `z-video-study-webpage-qwen` 的区别：音频没有画面，所以不抽帧，也不做多模态视觉分析；知识点改为绑定到音频里的 **MM:SS 时间戳**，HTML 里点时间戳就能 `audio.currentTime` 跳转播放。

## 适用场景

- 用户给本地音频（课堂录音、播客、讲座、会议录音、访谈），要求完整理解、做学习总结网页。
- 用户给主流平台音频链接并要求下载后理解；先下载到本地音频再用本 skill。
- 用户明确要求"知识点要能跳回原音频时间点"，优先用本 skill。
- 用户提到 DashScope、Qwen、`qwen3.7-plus`、OpenAI-compatible base_url，也用本 skill。

## 安全约定

- API Key 只从环境变量读取，默认变量名：`DASHSCOPE_API_KEY`。
- 不要把用户给的 key 写入 `SKILL.md`、脚本、报告、HTML、终端日志或最终回复。
- 默认 base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`。
- 默认模型：`qwen3.7-plus`（文本模型即可，无需多模态）。若返回模型不存在，提醒用户用 `--model` 改成实际可用模型名。

## 输入输出

输入：

- 本地音频：`/path/to/audio.mp3`（支持 mp3/wav/m4a/aac/ogg/flac/oga/opus/wma）
- 已下载音频所在目录
- 平台链接：先下载得到本地音频

默认输出在音频同级目录或指定目录：

```text
study-audio/
├── study-summary-audio.html     # 最终学习网页
├── qwen-analysis.json           # 模型结构化结果
├── qwen-segments.json           # 分段结果
├── transcript.txt               # 完整转录文本，若成功
├── transcript.json              # 带时间戳转录，若成功
├── assets/
│   └── audio-asr.wav            # 16k 单声道，给 ASR 用
└── run-report.json
```

> 原音频文件会被拷贝到输出目录，供网页 `<audio>` 直接本地播放，无需外链。

## 环境依赖

- **Python 3.11+**（需安装 `requests`）
- **ffmpeg / ffprobe**：必须在系统 PATH 中可用（Windows 可从 https://ffmpeg.org 下载）
- **转写后端（四选一，见下）**：
  - `vosk`（本地，**本机首选**）：`pip install vosk soundfile`（清华镜像），不依赖 torch / ctranslate2，模型自包含。中文小模型 `vosk-model-small-cn-0.22`（~42MB）从 https://alphacephei.com/vosk/models 下载，用 `--vosk-model <模型目录>` 指定。**适合 torch DLL 被安全软件拦截、或 ctranslate2 段错误的机器**。
  - `whisper`（本地，优先 `faster-whisper`：`pip install faster-whisper`；未装则回退 `openai-whisper`）。通用解，但本机实测两种 whisper 都跑不起来（见坑位）。
  - `dashscope`（云端）：用 `DASHSCOPE_API_KEY` 调 paraformer-v2 文件转写。**前提**：该 key 必须已开通 DashScope「文件转写」服务权限；且 Qwen-Audio 免费额度易耗尽，云端 ASR 在免费 key 上基本不可用。
  - 直接喂现成 `--transcript`（最稳，零依赖）
- **DashScope API Key**：环境变量 `DASHSCOPE_API_KEY`（仅做 Qwen 文本分析时普通对话 key 即可；DashScope 云端 ASR / Qwen-Audio 需额外服务权限或付费额度，免费 key 通常走不通）。

## 给朋友的一键上手（最快路径）

别人装好技能后，只需两步：

```bash
# 1) 一次性准备环境（装依赖 + 预热 Vosk 中文模型，约 1 分钟）
python "$HOME/.workbuddy/skills/z-audio-study-webpage-qwen/scripts/setup.py"

# 2) 转网页（默认 --asr auto，自动用 Vosk 本地转写，无需手动下模型/选后端）
export DASHSCOPE_API_KEY="你的key"   # 仅做 Qwen 分析需要
python "$HOME/.workbuddy/skills/z-audio-study-webpage-qwen/scripts/audio_study.py" \
  --audio "/path/to/audio.mp3" --title "音频主题"
```

- `setup.py` 用**清华镜像**装依赖并自动下载 `vosk-model-small-cn-0.22` 到 `~/.cache/vosk-models/`。
- 由于默认 `--asr auto`（Vosk → Whisper → DashScope 兜底），朋友**不用关心后端和模型路径**，直接给音频就能出网页。
- Vosk 模型若没预热，`--asr auto`/`--asr vosk` 运行时也会自动下载一次（缓存后免联网）。

## 推荐命令

### Windows / WorkBuddy

```powershell
# 设置 API Key（仅当前会话）
$env:DASHSCOPE_API_KEY = "你的key，不要写进文件"

# 方式 A：用 DashScope 云端 ASR 自动转写 + Qwen 分析（推荐，零本地模型）
python "$HOME\.workbuddy\skills\z-audio-study-webpage-qwen\scripts\audio_study.py" `
  --audio "C:\path\to\audio.mp3" `
  --title "音频主题" `
  --out-dir "C:\path\to\output\study-audio" `
  --asr dashscope `
  --model "qwen3.7-plus"

# 方式 B：用本地 Whisper 转写
python "$HOME\.workbuddy\skills\z-audio-study-webpage-qwen\scripts\audio_study.py" `
  --audio "C:\path\to\audio.mp3" --title "音频主题" --asr whisper

# 方式 B2（本机首选）：用本地 Vosk 离线转写（无需 torch / 云端权限）
python "$HOME\.workbuddy\skills\z-audio-study-webpage-qwen\scripts\audio_study.py" `
  --audio "C:\path\to\audio.mp3" --title "音频主题" `
  --asr vosk --vosk-model "C:\path\to\vosk-model-small-cn-0.22"

# 方式 C：已有转写文本，直接分析
python "$HOME\.workbuddy\skills\z-audio-study-webpage-qwen\scripts\audio_study.py" `
  --audio "C:\path\to\audio.mp3" --transcript "C:\path\to\transcript.txt" --title "音频主题"
```

### macOS / Linux

```bash
export DASHSCOPE_API_KEY="放在你本机环境里，不要写进文件"

python3 ~/.workbuddy/skills/z-audio-study-webpage-qwen/scripts/audio_study.py \
  --audio "/path/to/audio.mp3" \
  --title "音频主题" \
  --out-dir "/path/to/output/study-audio" \
  --asr dashscope
```

只验证网页模板，不调用模型（无需 API Key、无需转写）：

```bash
python3 ~/.workbuddy/skills/z-audio-study-webpage-qwen/scripts/audio_study.py \
  --audio "/path/to/audio.mp3" \
  --title "音频主题" \
  --mock-analysis
```

## 已知限制与坑位（已实测）

- **DashScope 文件转写权限**：`--asr dashscope` 走 `/api/v1/services/audio/asr/transcription`（异步）。该 key 必须有「文件转写」服务权限；纯对话 key 会 `AccessDenied: current user api does not support synchronous calls`。**对策**：换 `--asr whisper`（本地 faster-whisper，通用）。
- **DashScope 兼容模式不支持音频转写**：`/compatible-mode/v1/audio/transcriptions` 对 paraformer/sensevoice 系列返回连接重置（未实现），不要走这条。
- **`file_urls` 必须是数组**：DashScope 文件转写提交体的 `input.file_urls` 是数组 `["https://dashscope-result.oss-cn-beijing.aliyuncs.com/<file_id>"]`，不是 `{"1": url}` 字典，否则 `InvalidParameter: file_urls must be array`。
- **上传返回结构**：`POST /api/v1/files` 成功时 `file_id` 在 `data.uploaded_files[0].file_id`（不是 `data.file_id`）。
- **Whisper 后端（本机实测两种都跑不起来，建议直接上 Vosk）**：脚本优先 `faster-whisper`（CPU），失败回退 `openai-whisper`（PyTorch 引擎）。
  - ⚠️ **ctranslate2 段错误（已实测）**：本机 `faster-whisper` 加载模型即原生段错误（EXIT 139，非 Python 可捕获），报 `ctranslate2 ... Segmentation fault`。
  - ⚠️ **torch DLL 被拦（已实测）**：本机 `openai-whisper` 依赖的 torch 加载失败，`ImportError: DLL load failed while importing _C` / `WinError 1114`（第三方安全软件拦截 torch 的 DLL）。`pip install torch` 即便装上也无法 `import`。
  - ⚠️ **whisper-onnx 不兼容 Python 3.13**（managed 运行时即 3.13），请勿走此路。
  - **结论**：本机本地 ASR 走 **Vosk**（纯 C++ Kaldi，无 torch / ctranslate2），见下方 Vosk 段。
  - 中文准确率：`small` / `medium` 优于 `base`（whisper 路线仅作其它机器参考）。
- **Vosk 后端（本机本地 ASR 的可用解）**：
  - 安装：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple vosk soundfile`（**必须用清华镜像**，本机直连 PyPI 会长时间卡死无输出）。
  - 模型：中文小模型 `vosk-model-small-cn-0.22`（zip，约 42MB），从 https://alphacephei.com/vosk/models 下载解压，用 `--vosk-model <目录>` 指定。注意文件名是 `-0.22.zip`，不是 `-3.tar.gz`。
  - Vosk 小模型中文分词会在词间加空格（如「欢迎 关注 公众 号」），且偶有错字（如把「京灵智创」识别成「精灵痔疮」）；Qwen 分析时通常能结合上下文纠正，最终网页内容基本准确。
  - Vosk 不需要 GPU，CPU 上 8 秒音频转写 < 1 秒。
- **pip 镜像坑（本机）**：直连 `pip install` 到 PyPI 会卡死（无输出、长时间 running）。**一律加** `-i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn`。
- ASR 抛异常时脚本会把脱敏原因打到 stderr（`asr-failed:...`），便于排错。
- **分段数修复（已实测）**：旧逻辑对短音频（如 8 秒）也按 `--max-segments` 切成 12 段，导致串行打 13 次 Qwen 调用、在免费额度限流下卡死。已改为「每段至少约 30 秒」，8 秒音频只切 1 段 → 共 2 次调用（1 段 + 1 全局合成），秒级完成。长音频仍按 max_segments 上限切。
- **Qwen 文本分析额度**：`qwen3.7-plus` 对话端点（compatible-mode）普通 key 通常可用；但 DashScope「文件转写」与 Qwen-Audio 走免费额度时易 `403 Free allocated quota exceeded`。所以**云端 ASR 与 Qwen-Audio 在免费 key 上基本不可用，本地 Vosk 是唯一出路**。

## 执行流程

1. **确认音频本地路径**：如果用户给的是 URL，先下载到本地音频。找到实际文件后再执行本 skill。

2. **准备音频**：用 ffmpeg 转一份 16k 单声道 wav（`assets/audio-asr.wav`）给 ASR；原音频拷到输出目录供播放器用。

3. **转写（三选一）**：
   - 优先用用户提供的 `--transcript`（最稳）。
   - 否则按 `--asr` 选择后端：`dashscope`（云端 paraformer-v2，需 `DASHSCOPE_API_KEY`）或 `whisper`（本地）。
   - 转写失败/缺失时，报告中标注"缺少全文转录，结论更依赖标题信息"。

4. **Qwen 逐段分析**：按音频时长均分成最多 `--max-segments` 段，每段把对应窗口的转写文本发给 Qwen，要求输出 JSON：段主题、关键知识点（**带 MM:SS 时间戳**）、证据、待确认信息。

5. **全局学习结构合成**：再调用一次 Qwen，把分段结果合成为：30 秒总览、学习地图、关键知识点 × 时间戳、时间线、框架矩阵、复盘问题、行动清单、局限与待核验。

6. **渲染 HTML**：沿用学习网页模板；知识点卡片与时间线节点都带可点击时间戳按钮，点一下 `audio.currentTime = 该秒数` 并播放；末尾附完整转写文本（每行时间戳可点击跳转）。

7. **收尾检查**：校验 HTML 本地媒体路径存在；校验 `qwen-analysis.json` 可解析；检查没有把 API key 写入任何输出文件。

## 质量标准

- 不能只用音频标题泛泛总结。
- 关键知识点要来自转写文本，且绑定到真实时间戳（MM:SS）。
- 对不确定内容要标注"待核验"，不要伪装成事实。
- 时间戳必须可点击跳转，回听即能验证。

## 已验证的运行要点（长音频 / Windows / 沙箱）

- **沙箱外运行**：WorkBuddy 沙箱会拦截 dashscope 网络与部分目录写入，运行命令需 `dangerouslyDisableSandbox: true`。
- **Windows 路径写法**：传给 python 的 `--audio / --out-dir` 用 Windows 原生 `C:/Users/...` 形式。若写成 MSYS 的 `/c/Users/...`，Windows 版 python 会误解析为 `c:\c\Users\...` 而找不到文件。
- **长音频务必串行、前台、长超时**：单音频 = (段数 + 1) 次 Qwen 调用，每段 ~30s，请逐个前台运行，并配 `timeout 600000`（10 分钟）。并行会触发接口限速。
- **避开 __pycache__ 写入拦截**：若以 `import` 方式调用脚本，沙箱可能拦截往技能目录写 `__pycache__`，可先把脚本复制到可写目录（如工作区）再运行。
- **DashScope ASR 需要网络**：`--asr dashscope` 会上传音频到 DashScope 并轮询结果；网络不可达时用 `--transcript` 喂现成文本最稳。

## 测试

编辑脚本后运行：

```bash
python3 -m py_compile \
  ~/.workbuddy/skills/z-audio-study-webpage-qwen/scripts/audio_study.py \
  ~/.workbuddy/skills/z-audio-study-webpage-qwen/tests/test_audio_study.py

python3 ~/.workbuddy/skills/z-audio-study-webpage-qwen/tests/test_audio_study.py
```
