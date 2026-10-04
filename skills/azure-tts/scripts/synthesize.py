#!/usr/bin/env python3
"""Synthesize one Chinese courseware narration clip with Azure Speech SDK.

The script intentionally supports the project's historical env aliases without
printing their values. It does not synthesize or modify AI-video audio.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys


def load_simple_env(path: pathlib.Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--text-file", type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--rate", default="0%", help="SSML rate, e.g. -5%%")
    parser.add_argument("--pitch", default="0Hz")
    args = parser.parse_args()

    project_env = pathlib.Path.cwd() / ".env"
    load_simple_env(project_env)
    shared_env = pathlib.Path.home() / ".codex-ppt-skill" / ".env"
    load_simple_env(shared_env)

    region = first_env("AZURE_SPEECH_REGION", "AZURE_AREA", "azure_area")
    key = first_env("AZURE_SPEECH_KEY", "AZURE_KEY", "axure_secret")
    if not region or not key:
        print("Azure Speech 配置缺失：需要 Azure Speech region 和 key。未读取到密钥值。", file=sys.stderr)
        return 2

    if bool(args.text) == bool(args.text_file):
        print("请二选一提供 --text 或 --text-file。", file=sys.stderr)
        return 2
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    text = text.strip()
    if not text:
        print("旁白文本为空。", file=sys.stderr)
        return 2

    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        print("未安装 Azure Speech SDK，请安装 azure-cognitiveservices-speech。", file=sys.stderr)
        return 3

    args.out.parent.mkdir(parents=True, exist_ok=True)
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = args.voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3
    )
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(args.out))
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    safe_text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    ssml = (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">'
        f'<voice name="{args.voice}"><prosody rate="{args.rate}" pitch="{args.pitch}">{safe_text}</prosody>'
        "</voice></speak>"
    )
    result = synthesizer.speak_ssml_async(ssml).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"generated={args.out} voice={args.voice}")
        return 0
    details = getattr(result, "cancellation_details", None)
    reason = getattr(details, "reason", "unknown")
    print(f"Azure Speech synthesis failed: {reason}", file=sys.stderr)
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
