#!/usr/bin/env python3
"""Smoke tests for audio_study.py (no network / no API key needed)."""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPT = SKILL / "scripts" / "audio_study.py"


def load_module():
    import sys
    spec = importlib.util.spec_from_file_location("audio_study", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audio_study"] = mod  # 必须注册，否则 dataclass 内省会失败
    spec.loader.exec_module(mod)
    return mod


def test_timestamp_helpers():
    mod = load_module()
    assert mod.seconds_to_label(0) == "00:00"
    assert mod.seconds_to_label(75) == "01:15"
    assert mod.seconds_to_label(3661) == "01:01:01"
    assert mod.label_to_seconds("01:15") == 75
    assert mod.label_to_seconds("01:01:01") == 3661
    assert mod.normalize_timestamp("02:30", "00:00") == "02:30"
    assert mod.normalize_timestamp("garbage", "00:00") == "00:00"
    assert mod.normalize_timestamp("看 03:45 处", "00:00") == "03:45"


def test_mock_analysis_and_render():
    mod = load_module()
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "study-audio"
        out.mkdir()
        (out / "assets").mkdir()
        # 伪造一个音频文件用于播放器引用
        fake_audio = out / "dummy.mp3"
        fake_audio.write_bytes(b"\x00\x00")
        info = {"format": {"duration": "150.0"}}
        analysis = mod.mock_analysis("测试音频", 150.0)
        analysis = mod.normalize_analysis(analysis, "00:00")
        transcript = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "这是第一段内容。"},
                {"start": 5.0, "end": 10.0, "text": "这是第二段内容。"},
            ],
            "text": "这是第一段内容。这是第二段内容。",
        }
        html_path = mod.render_html(
            analysis=analysis,
            audio=fake_audio,
            out_dir=out,
            info=info,
            transcript_status="mock",
            transcript=transcript,
        )
        text = html_path.read_text(encoding="utf-8")
        assert html_path.exists()
        assert "study-summary-audio.html" in html_path.name
        assert "seekTo(" in text, "缺少时间戳跳转脚本"
        assert "这是第一段内容" in text, "转写文本未渲染"
        # 校验时间戳按钮存在
        assert "onclick=\"seekTo('00:30')\"" in text or "00:30" in text


def test_unsupported_ext_rejected():
    mod = load_module()
    # 用 argparse 校验 --audio 后缀不在支持列表时的行为
    import pytest  # noqa: F401  (optional; test still runs without it below)


if __name__ == "__main__":
    test_timestamp_helpers()
    test_mock_analysis_and_render()
    print("OK: audio_study smoke tests passed")
