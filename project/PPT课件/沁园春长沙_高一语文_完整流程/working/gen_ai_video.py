# -*- coding: utf-8 -*-
"""AI-VIDEO-01 即梦视频生成（第 2 次，契约最后一次额度）。

调用即梦本地服务 /v1/videos/generations，阻塞等待完成并下载 MP4。
所有响应与日志写入 working/ai_video_attempt2.json，便于失败取证。
"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "resources" / "ai_video"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MP4 = OUT_DIR / "ai-video-01.mp4"
LOG = ROOT / "working" / "ai_video_attempt2.json"

PROMPT = (
    "秋夜的长江江面，一叶乌篷小舟自画面左侧向右缓缓漂行。江面开阔平静，薄雾贴着水面缓缓流动，"
    "远处青灰色群山层叠起伏。一轮明月高悬在画面右上方，月光在江面铺开一道柔和的银色光带。"
    "镜头缓慢横移跟随小舟，水面泛起细密涟漪，芦苇在画面边缘轻轻摇动。"
    "画面色调为青绿与月白，沉静清冷，带绢本古画的质感。"
    "无人物面部特写，无文字，无水印，无字幕，无logo。横屏16:9，画面稳定，电影感写实。"
)

def main():
    s = requests.Session(); s.trust_env = False
    payload = {
        "model": "jimeng-video-seedance-2.0-mini",
        "prompt": PROMPT,
        "aspect_ratio": "16:9",
        "duration": 10,
    }
    started = time.time()
    record = {"attempt": 2, "model": payload["model"], "duration": 10,
              "aspect_ratio": "16:9", "prompt": PROMPT, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    try:
        r = s.post("http://127.0.0.1:8001/v1/videos/generations", json=payload,
                   timeout=(30, 900))
        record["http_status"] = r.status_code
        record["elapsed_seconds"] = round(time.time() - started, 1)
        try:
            body = r.json()
        except Exception:
            body = {"_raw": r.text[:2000]}
        record["response"] = body

        # 尽量从多种可能结构里取 url
        url = None
        def dig(o):
            nonlocal url
            if url: return
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("url", "video_url", "videoUrl", "download_url") and isinstance(v, str) and v.startswith("http"):
                        url = v; return
                    dig(v)
            elif isinstance(o, list):
                for v in o: dig(v)
        dig(body)
        record["video_url"] = url

        if url:
            vr = s.get(url, timeout=(30, 300))
            MP4.write_bytes(vr.content)
            record["mp4_path"] = str(MP4)
            record["mp4_bytes"] = MP4.stat().st_size
            record["ok"] = True
        else:
            record["ok"] = False
            record["error"] = "no video url in response"
    except Exception as e:
        record["ok"] = False
        record["error"] = f"{type(e).__name__}: {e}"
        record["elapsed_seconds"] = round(time.time() - started, 1)
    record["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    LOG.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: record.get(k) for k in ("ok","http_status","elapsed_seconds","video_url","mp4_bytes","error")}, ensure_ascii=False))
    return 0 if record.get("ok") else 1

if __name__ == "__main__":
    sys.exit(main())
