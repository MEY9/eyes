#!/usr/bin/env python3
"""xiaohongshu-mcp 调用器：搜索/详情/登录检查，含媒体下载。

用法:
  python xhs_call.py status
  python xhs_call.py qrcode --save qr.png
  python xhs_call.py search --keyword "高中生物课件" --save out.json [--covers dir] [--top 10]
  python xhs_call.py detail --feed-id ID --xsec-token TOK --save out.json [--images dir]

所有请求经 UTF-8 JSON-RPC 直调 http://localhost:18060/mcp；不要用 shell 内联中文参数。
"""
import argparse
import base64
import json
import re
import sys
import time
from pathlib import Path

import requests

MCP = "http://localhost:18060/mcp"
READONLY = {"check_login_status", "get_login_qrcode", "search_feeds", "get_feed_detail", "user_profile", "list_feeds"}


def call(name: str, arguments: dict, timeout: int = 120):
    if name not in READONLY:
        raise SystemExit(f"拒绝调用非只读工具: {name}")
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": arguments}}
    r = requests.post(MCP, json=payload, timeout=timeout)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise SystemExit(f"MCP error: {body['error']}")
    return body["result"]["content"]


def save_text(text: str, path: str | None):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
        print(f"saved: {path}")
    return text


def download(url: str, path: Path) -> int:
    r = requests.get(url, timeout=60)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return len(r.content)


def cmd_status(_a):
    text = call("check_login_status", {})[0]["text"]
    print(text)
    if "已登录" not in text:
        raise SystemExit("未登录：先 `python xhs_call.py qrcode --save qr.png` 扫码")


def cmd_qrcode(a):
    parts = call("get_login_qrcode", {}, timeout=90)
    for part in parts:
        if part.get("type") == "image":
            data = base64.b64decode(part["data"])
            Path(a.save).parent.mkdir(parents=True, exist_ok=True)
            Path(a.save).write_bytes(data)
            print(f"二维码已保存: {a.save}（约3分钟有效，用小红书App扫码）")
            return
    raise SystemExit("响应中没有二维码图片")


def cmd_search(a):
    text = call("search_feeds", {"keyword": a.keyword})[0]["text"]
    text = save_text(text, a.save)
    feeds = json.loads(text)["feeds"]
    feeds.sort(key=lambda f: _interact_num(f), reverse=True)
    print(f"共 {len(feeds)} 条，按互动数排序：")
    for f in feeds[: a.top]:
        nc, ii = f.get("noteCard", {}), f.get("noteCard", {}).get("interactInfo", {})
        print(f"  赞{ii.get('likedCount','?'):>5} 藏{ii.get('collectedCount','?'):>5} 评{ii.get('commentCount','?'):>4} "
              f"| {nc.get('displayTitle','')[:38]:<40} | {nc.get('user',{}).get('nickname','')}")
        print(f"        id={f['id']} xsec={f.get('xsecToken','')[:24]}...")
    if a.covers:
        n = 0
        for f in feeds[: a.top]:
            url = (f.get("noteCard", {}).get("cover", {}) or {}).get("urlDefault")
            if not url:
                continue
            time.sleep(3)
            n += 1
            size = download(url, Path(a.covers) / f"cover_{n:02d}_{f['id'][:8]}.jpg")
            print(f"  cover -> {a.covers}/cover_{n:02d}_{f['id'][:8]}.jpg ({size}B)")


def _interact_num(feed):
    ii = feed.get("noteCard", {}).get("interactInfo", {}) or {}

    def num(v):
        try:
            return int(str(v))
        except (TypeError, ValueError):
            m = re.match(r"([\d.]+)([万w]?)", str(v) or "")
            if not m:
                return 0
            return int(float(m.group(1)) * (10000 if m.group(2) else 1))
    return sum(num(ii.get(k)) for k in ("likedCount", "collectedCount", "commentCount"))


def cmd_detail(a):
    parts = call("get_feed_detail",
                 {"feed_id": a.feed_id, "xsec_token": a.xsec_token})
    text = next((p["text"] for p in parts if p.get("type") == "text"), "")
    text = save_text(text, a.save)
    j = json.loads(text)
    note = j.get("data", {}).get("note", {})
    ii = note.get("interactInfo", {}) or {}
    print(f"标题: {note.get('title')}")
    print(f"类型: {note.get('type')} | 赞 {ii.get('likedCount')} 藏 {ii.get('collectedCount')} 评 {ii.get('commentCount')}")
    print(f"正文: {(note.get('desc') or '')[:160]}")
    if a.images:
        n = 0
        for im in note.get("imageList") or []:
            url = im.get("urlDefault") or im.get("url")
            if not url:
                continue
            time.sleep(3)
            n += 1
            size = download(url, Path(a.images) / f"img_{n:02d}.jpg")
            print(f"  image -> {a.images}/img_{n:02d}.jpg ({size}B)")
    if a.images:
        for part in parts:
            if part.get("type") == "image":
                n += 1
                ext = part.get("mimeType", "image/jpeg").split("/")[-1].replace("jpeg", "jpg")
                Path(a.images).mkdir(parents=True, exist_ok=True)
                Path(a.images, f"img_{n:02d}.{ext}").write_bytes(base64.b64decode(part["data"]))
                print(f"  inline image -> {a.images}/img_{n:02d}.{ext}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    q = sub.add_parser("qrcode"); q.add_argument("--save", default="qr.png"); q.set_defaults(fn=cmd_qrcode)
    s = sub.add_parser("search")
    s.add_argument("--keyword", required=True)
    s.add_argument("--save", help="原始 JSON 保存路径")
    s.add_argument("--covers", help="封面下载目录")
    s.add_argument("--top", type=int, default=10)
    s.set_defaults(fn=cmd_search)
    d = sub.add_parser("detail")
    d.add_argument("--feed-id", required=True)
    d.add_argument("--xsec-token", required=True)
    d.add_argument("--save", help="原始 JSON 保存路径")
    d.add_argument("--images", help="图片下载目录")
    d.set_defaults(fn=cmd_detail)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
