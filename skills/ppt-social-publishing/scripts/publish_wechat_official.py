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
import shutil
import subprocess
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
    request_kwargs: Dict[str, Any] = {
        "params": params,
        "timeout": 120,
    }
    if files:
        request_kwargs["data"] = form_data
        request_kwargs["files"] = files
    elif json_body is not None:
        # WeChat's article endpoint has been observed to persist requests'
        # default ASCII JSON escapes literally. Send real UTF-8 JSON instead.
        request_kwargs["data"] = json.dumps(
            json_body, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        request_kwargs["headers"] = {"Content-Type": "application/json"}
    elif form_data is not None:
        request_kwargs["data"] = form_data
    response = requests.request(method, root + path, **request_kwargs)
    response.raise_for_status()
    # The WeChat API often labels JSON responses as text/plain without a
    # charset. Decode the raw bytes as UTF-8 before parsing, otherwise Chinese
    # text is misread as ISO-8859-1 mojibake during draft verification.
    try:
        payload = json.loads(response.content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
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


def make_wechat_safe_image(file_path: Path, work_dir: Path) -> Path:
    """Return an article-image upload copy below the one-mebibyte contract.

    Slides should already comply.  Animated GIFs occasionally do not, so make
    a publication-only copy rather than changing the approved project asset.
    """
    if file_path.stat().st_size < 1 * 1024 * 1024:
        return file_path
    if file_path.suffix.lower() != ".gif":
        raise SystemExit(f"article image must be smaller than 1 MiB: {file_path}")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit(f"animated GIF exceeds 1 MiB and ffmpeg is unavailable: {file_path}")
    work_dir.mkdir(parents=True, exist_ok=True)
    target = work_dir / f"{file_path.stem}_wechat.gif"
    # Keep the demonstration animated, while reducing the publication copy's
    # sampling rate and width.  Do not mutate the source animation.
    command = [
        ffmpeg, "-y", "-i", str(file_path), "-vf",
        "fps=4,scale='min(480,iw)':-2:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=32[p];[s1][p]paletteuse=dither=none",
        "-loop", "0", str(target),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not target.is_file() or target.stat().st_size >= 1 * 1024 * 1024:
        raise SystemExit(f"could not create a GIF below 1 MiB for WeChat: {file_path}")
    return target


def upload_article_image(token: str, file_path: Path, upload_work_dir: Path) -> str:
    """Upload an image for direct use in article HTML."""
    if not file_path.is_file():
        raise SystemExit(f"file not found: {file_path}")
    upload_path = make_wechat_safe_image(file_path, upload_work_dir)
    suffix = upload_path.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".gif"}:
        raise SystemExit(f"article image must be jpg/png/gif: {file_path}")
    mime = {".png": "image/png", ".gif": "image/gif"}.get(suffix, "image/jpeg")
    with upload_path.open("rb") as handle:
        payload = request_json(
            "POST",
            "/cgi-bin/media/uploadimg",
            params={"access_token": token},
            files={"media": (upload_path.name, handle, mime)},
            json_body=None,
            form_data=None,
        )
    return payload["url"]


def validate_copy(copy_text: str) -> list[str]:
    lines = [line.strip() for line in copy_text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise SystemExit("copy.txt must contain exactly one non-empty course-information line")
    if not lines[0].startswith("教材：") or "年级：" not in lines[0] or "册" not in lines[0]:
        raise SystemExit("copy.txt first line must contain 教材、年级和上/下册")
    if len(lines[0]) > 120:
        raise SystemExit("copy.txt first line is unexpectedly long")
    return lines


def build_article(lines: Iterable[str], image_urls: Iterable[str] = ()) -> str:
    summary = html.escape(next(iter(lines)))
    slides = "\n".join(
        f'  <p style="margin:16px 0 0;"><img src="{html.escape(url, quote=True)}" '
        'style="display:block;width:100%;height:auto;" /></p>'
        for url in image_urls
    )
    return f'''<section style="background:#FBF8F2;padding:24px 20px;color:#20252B;line-height:1.8;font-size:16px;">
  <p style="margin:0 0 8px;">{summary}</p>
{slides}
</section>'''


def upload_article_assets(token: str, article_html: str, asset_root: Path,
                          upload_work_dir: Path) -> tuple[str, int]:
    """Upload each local `<img>` source and substitute its WeChat URL.

    The approved showcase article intentionally repeats a few slide images. A
    path-to-URL map preserves those repeats in HTML without re-uploading them.
    """
    source_pattern = re.compile(r'(<img\b[^>]*\bsrc=["\'])([^"\']+)(["\'])', re.I)
    uploaded: Dict[str, str] = {}
    image_nodes = 0

    def substitute(match: re.Match[str]) -> str:
        nonlocal image_nodes
        image_nodes += 1
        source = match.group(2)
        if re.match(r"https?://", source, re.I):
            return match.group(0)
        relative = Path(source.replace("/", os.sep))
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit(f"article image source must be a safe relative path: {source}")
        asset_path = (asset_root / relative).resolve()
        try:
            asset_path.relative_to(asset_root.resolve())
        except ValueError as exc:
            raise SystemExit(f"article image escaped asset root: {source}") from exc
        key = str(asset_path).lower()
        if key not in uploaded:
            uploaded[key] = upload_article_image(token, asset_path, upload_work_dir)
        return f"{match.group(1)}{uploaded[key]}{match.group(3)}"

    rendered = source_pattern.sub(substitute, article_html)
    if image_nodes == 0:
        raise SystemExit("custom article must contain at least one <img> node")
    return rendered, image_nodes


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
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--slides-dir", required=True, type=Path,
                        help="Directory containing ordered slide_*.jpg/png images")
    parser.add_argument("--article-file", type=Path,
                        help="Approved rich article HTML. Local img sources are uploaded and replaced.")
    parser.add_argument("--asset-root", type=Path,
                        help="Root for local img sources in --article-file (defaults to that file's folder)")
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
        article = (args.article_file.read_text(encoding="utf-8")
                   if args.article_file else build_article(lines))
        (args.output_dir / "article.html").write_text(article, encoding="utf-8")
        (args.output_dir / "article.md").write_text(
            "\n".join(lines) +
            "\n", encoding="utf-8")
        print(json.dumps({"status": "dry_run", "article_path": str(args.output_dir / "article.html")}, ensure_ascii=False))
        return 0

    app_id = require_env("WECHAT_MP_APPID", "WECHAT_APP_ID")
    app_secret = require_env("WECHAT_MP_APPSECRET", "WECHAT_APP_SECRET")
    token = get_access_token(app_id, app_secret)
    cover_id = upload_permanent(token, args.cover, "thumb")
    slide_paths = sorted(
        [*args.slides_dir.glob("slide_*.jpg"), *args.slides_dir.glob("slide_*.jpeg"),
         *args.slides_dir.glob("slide_*.png")],
        key=lambda path: int(re.search(r"slide_(\d+)", path.stem).group(1))
        if re.search(r"slide_(\d+)", path.stem) else path.stem,
    )
    if not slide_paths:
        raise SystemExit(f"no slide images found in {args.slides_dir}")
    if args.article_file:
        if not args.article_file.is_file():
            raise SystemExit(f"article file not found: {args.article_file}")
        article_source = args.article_file.read_text(encoding="utf-8")
        if re.search(r"<\s*(video|script|iframe)\b", article_source, re.I):
            raise SystemExit("custom article may not contain video, script, or iframe nodes")
        asset_root = (args.asset_root or args.article_file.parent).resolve()
        if not asset_root.is_dir():
            raise SystemExit(f"article asset root not found: {asset_root}")
        article, expected_image_count = upload_article_assets(
            token, article_source, asset_root, args.output_dir / ".wechat_upload_assets"
        )
    else:
        slide_urls = [upload_article_image(token, path, args.output_dir / ".wechat_upload_assets")
                      for path in slide_paths]
        article = build_article(lines, slide_urls)
        expected_image_count = len(slide_paths)
    if re.search(r'\bsrc=["\'](?!https?://)', article, re.I):
        raise RuntimeError("article still contains a non-WeChat image source")
    (args.output_dir / "article.html").write_text(article, encoding="utf-8")
    (args.output_dir / "article.md").write_text(
        "\n".join(lines) +
        "\n", encoding="utf-8")

    draft_id = add_draft(token, args.title, article, cover_id, lines[0])
    draft = get_draft(token, draft_id)
    draft_text = json.dumps(draft, ensure_ascii=False)
    if "教材：" not in draft_text:
        raise RuntimeError("draft verification failed: WeChat did not retain the Chinese article text")
    if draft_text.count("<img") < expected_image_count:
        raise RuntimeError("draft verification failed: WeChat did not retain all article images")

    result: Dict[str, Any] = {
        "status": "draft_created",
        "draft_media_id": draft_id,
        "article_path": str(args.output_dir / "article.html"),
        "cover_media_id": cover_id,
        "slide_count": len(slide_paths),
        "article_image_count": expected_image_count,
    }
    (args.output_dir / "publish_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.mode == "publish":
        try:
            submitted = publish(token, draft_id)
        except RuntimeError as exc:
            if "48001" in str(exc):
                result["status"] = "draft_created_publish_unauthorized_48001"
                (args.output_dir / "publish_result.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(result, ensure_ascii=False))
                return 2
            raise
        result["publish_id"] = submitted["publish_id"]
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
