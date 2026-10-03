#!/usr/bin/env python3
"""Print a public WeChat article as JSON without creating intermediate files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen


MAX_HTML_BYTES = 8 * 1024 * 1024
BLOCK_TAGS = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "li"}
SKIP_TAGS = {"script", "style", "noscript", "svg"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.author = ""
        self.in_content = False
        self.content_depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta":
            name = values.get("name") or values.get("property") or ""
            value = (values.get("content") or "").strip()
            if name in {"og:title", "twitter:title"} and not self.title:
                self.title = value
            elif name in {"author", "og:article:author"} and not self.author:
                self.author = value

        if not self.in_content and values.get("id") == "js_content":
            self.in_content = True
            self.content_depth = 1
            return
        if not self.in_content:
            return

        if tag not in VOID_TAGS:
            self.content_depth += 1
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        elif not self.skip_depth:
            if tag == "br" or tag in BLOCK_TAGS:
                self.parts.append("\n")
            elif tag == "img":
                source = values.get("data-src") or values.get("src") or ""
                if source and source not in self.images:
                    self.images.append(source)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.in_content and tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_content:
            return
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        elif not self.skip_depth and tag in BLOCK_TAGS:
            self.parts.append("\n")
        self.content_depth -= 1
        if self.content_depth == 0:
            self.in_content = False

    def handle_data(self, data: str) -> None:
        if self.in_content and not self.skip_depth:
            text = re.sub(r"[\t\r\f\v ]+", " ", data)
            if text.strip():
                self.parts.append(text)


def download(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com":
        raise ValueError("URL must be a public article under https://mp.weixin.qq.com/")
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urlopen(request, timeout=20) as response:
        content_type = response.headers.get_content_type()
        data = response.read(MAX_HTML_BYTES + 1)
        if content_type != "text/html":
            raise ValueError(f"Expected HTML but received {content_type}")
        if len(data) > MAX_HTML_BYTES:
            raise ValueError("Page exceeds the 8 MiB read limit")
        charset = response.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def parse(html: str, url: str) -> dict[str, object]:
    parser = ArticleParser()
    parser.feed(html)
    raw = unescape("".join(parser.parts)).replace("\u200b", "")
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
    content = "\n\n".join(line for line in lines if line)
    if not parser.title or not content:
        raise ValueError("Article title or正文 was not found; the page may require verification")

    timestamp = re.search(r'(?:publish_time%22%3A|publish_time["\']?\s*[:=]\s*["\']?)(\d{10})', html)
    published_at = datetime.fromtimestamp(int(timestamp.group(1))).astimezone().isoformat(timespec="minutes") if timestamp else None
    return {
        "title": parser.title,
        "author": parser.author or None,
        "published_at": published_at,
        "url": url,
        "content": content,
        "images": parser.images,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("url", help="Public mp.weixin.qq.com article URL")
    args = arguments.parse_args()
    json.dump(parse(download(args.url), args.url), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
