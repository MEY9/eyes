#!/usr/bin/env python3
"""Create and optionally publish a WeChat Official Account article.

The script uses the official HTTP API only. It never prints or persists tokens.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import requests


API_ROOT = "https://api.weixin.qq.com"


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def require_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    raise SystemExit(f"missing environment variable: {' or '.join(names)}")


def request_json(method: str, path: str, *, params: Dict[str, str] | None = None,
                 json_body: Dict[str, Any] | None = None,
                 files: Dict[str, Tuple[str, Any, str]] | None = None,
                 form_data: Dict[str, str] | None = None) -> Dict[str, Any]:
    root = os.environ.get("WECHAT_API_BASE_URL", API_ROOT).rstrip("/")
    response = requests.request(method, root + path, params=params, json=json_body,
                                data=form_data, files=files, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if payload.get("errcode", 0) != 0:
        raise RuntimeError(f"WeChat API error {payload.get('errcode')}: {payload.get('errmsg')}")
    return payload


def get_access_token(app_id: str, app_secret: str) -> str:
    payload = request_json("GET", "/cgi-bin/token", params={
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret,
    })
    return payload["access_token"]


def upload_permanent(token: str, file_path: Path, media_type: str,
                     description: Dict[str, str] | None = None) -> str:
    if not file_path.is_file():
        raise SystemExit(f"file not found: {file_path}")
    if media_type == "video" and file_path.stat().st_size > 10 * 1024 * 1024:
        raise SystemExit("WeChat official API video material must be <= 10 MiB; create a compressed copy first")
    if media_type == "thumb" and file_path.stat().st_size > 64 * 1024:
        raise SystemExit("WeChat official API thumb material must be <= 64 KiB; create a compressed cover first")
    data: Dict[str, str] = {}
    if description:
        data["description"] = json.dumps(description, ensure_ascii=False)
    with file_path.open("rb") as handle:
        payload = request_json(
            "POST",
            "/cgi-bin/material/add_material",
            params={"access_token": token, "type": media_type},
            files={"media": (file_path.name, handle, "application/octet-stream")},
            json_body=None,
            form_data=data,
        )
    return payload["media_id"]


def validate_copy(copy_text: str) -> list[str]:
    lines = [line.strip() for line in copy_text.splitlines() if line.strip()]
    if len(lines) != 3:
        raise SystemExit("copy.txt must contain exactly three non-empty lines")
    if not lines[0].startswith("教材：") or "年级：" not in lines[0] or "册" not in lines[0]:
        raise SystemExit("copy.txt first line must contain 教材、年级和上/下册")
    summary_match = re.findall(r"【([^】]*)】", lines[0])
    if not summary_match or len(summary_match[-1]) > 50:
        raise SystemExit("the bracketed teaching summary must be present and <= 50 Chinese characters")
    if len(lines[0]) > 120:
        raise SystemExit("copy.txt first line is unexpectedly long")
    if lines[1] != "精研AI教育，接顶制":
        raise SystemExit("copy.txt second line must be 精研AI教育，接顶制")
    tags = lines[2].split()
    if len(tags) != 5 or any(not tag.startswith("#") for tag in tags):
        raise SystemExit("copy.txt third line must contain exactly five #tags")
    return lines


def build_article(title: str, lines: Iterable[str], video_id: str) -> str:
    summary, brand, tags = [html.escape(item) for item in lines]
    safe_video_id = html.escape(video_id, quote=True)
    video_src = (
        "https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl"
        f"&action=mpvideo&auto=0&vid={safe_video_id}"
    )
    return f'''<section style="background:#FBF8F2;padding:24px 20px;color:#20252B;line-height:1.8;font-size:16px;">
  <h1 style="font-size:22px;line-height:1.4;margin:0 0 20px;color:#20252B;">{html.escape(title)}</h1>
  <p style="margin:0 0 12px;color:#5C8D83;font-weight:700;">【教学设计总结内容】</p>
  <p style="margin:0 0 8px;">{summary}</p>
  <p style="margin:0 0 8px;">{brand}</p>
  <p style="margin:0 0 24px;color:#5C8D83;">{tags}</p>
  <p style="margin:0 0 12px;color:#5C8D83;font-weight:700;">【教学课件视频】</p>
  <iframe class="video_iframe rich_pages" data-vidtype="2" data-mpvid="{safe_video_id}"
    allowfullscreen="" frameborder="0" data-ratio="0.5625" data-w="1080"
    style="width:100%;border:0;display:block;"
    src="{video_src}"></iframe>
</section>'''


def add_draft(token: str, title: str, content: str, cover_id: str, digest: str) -> str:
    payload = request_json(
        "POST",
        "/cgi-bin/draft/add",
        params={"access_token": token},
        json_body={"articles": [{
            "article_type": "news",
            "title": title[:32],
            "author": "",
            "digest": digest[:120],
            "content": content,
            "thumb_media_id": cover_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]},
    )
    return payload["media_id"]


def get_draft(token: str, media_id: str) -> Dict[str, Any]:
    return request_json(
        "POST", "/cgi-bin/draft/get",
        params={"access_token": token},
        json_body={"media_id": media_id},
    )


def publish(token: str, media_id: str) -> Dict[str, Any]:
    return request_json(
        "POST", "/cgi-bin/freepublish/submit",
        params={"access_token": token},
        json_body={"media_id": media_id},
    )


def publish_status(token: str, publish_id: str) -> Dict[str, Any]:
    return request_json(
        "POST", "/cgi-bin/freepublish/get",
        params={"access_token": token},
        json_body={"publish_id": publish_id},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--copy-file", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--mode", choices=["draft", "publish"],
                        default=os.environ.get("WECHAT_MP_PUBLISH_MODE", "publish"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env(args.env_file)
    lines = validate_copy(args.copy_file.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        video_id = "wxv_dry_run"
        article = build_article(args.title, lines, video_id)
        (args.output_dir / "article.html").write_text(article, encoding="utf-8")
        (args.output_dir / "article.md").write_text(
            "【教学设计总结内容】\n\n" + "\n".join(lines) +
            "\n\n【教学课件视频】\n", encoding="utf-8")
        print(json.dumps({"status": "dry_run", "article_path": str(args.output_dir / "article.html")}, ensure_ascii=False))
        return 0

    app_id = require_env("WECHAT_MP_APPID", "WECHAT_APP_ID")
    app_secret = require_env("WECHAT_MP_APPSECRET", "WECHAT_APP_SECRET")
    token = get_access_token(app_id, app_secret)
    cover_id = upload_permanent(token, args.cover, "thumb")
    video_id = upload_permanent(token, args.video, "video", {
        "title": args.title[:64],
        "introduction": lines[0][:120],
    })
    article = build_article(args.title, lines, video_id)
    (args.output_dir / "article.html").write_text(article, encoding="utf-8")
    (args.output_dir / "article.md").write_text(
        "【教学设计总结内容】\n\n" + "\n".join(lines) +
        "\n\n【教学课件视频】\n", encoding="utf-8")

    draft_id = add_draft(token, args.title, article, cover_id, lines[0])
    draft = get_draft(token, draft_id)
    draft_text = json.dumps(draft, ensure_ascii=False)
    if "教学课件视频" not in draft_text or video_id not in draft_text:
        raise RuntimeError("draft verification failed: WeChat did not retain the teaching video node")

    result: Dict[str, Any] = {
        "status": "draft_created",
        "draft_media_id": draft_id,
        "article_path": str(args.output_dir / "article.html"),
        "cover_media_id": cover_id,
        "video_media_id": video_id,
    }
    if args.mode == "publish":
        submitted = publish(token, draft_id)
        result["publish_id"] = submitted["publish_id"]
        for _ in range(40):
            status = publish_status(token, submitted["publish_id"])
            publish_status_code = status.get("publish_status")
            if publish_status_code == 0:
                result.update({
                    "status": "published",
                    "article_id": status.get("article_id"),
                    "article_url": status.get("article_detail", {}).get("item", [{}])[0].get("article_url"),
                })
                break
            if publish_status_code in {2, 3, 4, 5, 6}:
                raise RuntimeError(f"WeChat publish failed with status {publish_status_code}")
            time.sleep(3)
        else:
            raise RuntimeError("WeChat publish status polling timed out")
    (args.output_dir / "publish_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
