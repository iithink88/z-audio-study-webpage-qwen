#!/usr/bin/env python3
"""一键准备 z-audio-study-webpage-qwen 的运行环境。

用法：
    python scripts/setup.py

做的事：
  1) 用清华镜像安装依赖（vosk / soundfile / requests）
  2) 预热下载 Vosk 中文小模型到 ~/.cache/vosk-models/
之后直接跑 audio_study.py 即可（默认 --asr auto，会自动用 Vosk 本地转写）。
"""
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PKGS = ["vosk", "soundfile", "requests"]
TSINGHUA = "https://pypi.tuna.tsinghua.edu.cn/simple"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
MODEL_DIR = Path.home() / ".cache" / "vosk-models" / "vosk-model-small-cn-0.22"


def pip_install() -> None:
    print("==> 安装依赖 (清华镜像)")
    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-i",
                TSINGHUA,
                "--trusted-host",
                "pypi.tuna.tsinghua.edu.cn",
                *PKGS,
            ]
        )
    except subprocess.CalledProcessError:
        print("   镜像安装失败，回退默认 PyPI 源")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *PKGS])


def download_model() -> None:
    if MODEL_DIR.exists() and any(MODEL_DIR.iterdir()):
        print(f"==> Vosk 模型已存在: {MODEL_DIR}")
        return
    print(f"==> 下载 Vosk 中文模型 {MODEL_URL}")
    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
    zip_path = MODEL_DIR.parent / "vosk-model-small-cn-0.22.zip"
    with urllib.request.urlopen(MODEL_URL, timeout=300) as resp:
        data = resp.read()
    zip_path.write_bytes(data)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(MODEL_DIR.parent)
    print(f"==> 模型就绪: {MODEL_DIR}")


if __name__ == "__main__":
    pip_install()
    download_model()
    print("\n环境准备完成。运行示例：")
    print('  python scripts/audio_study.py --audio "<音频路径>" --title "<标题>"')
    print("（默认 --asr auto，会自动用 Vosk 本地转写，无需手动下模型）")
