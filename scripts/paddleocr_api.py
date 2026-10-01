#!/usr/bin/env python3
"""Call the PaddleOCR AI Studio API and save structured OCR results.

The script intentionally uses requests instead of MCP. Credentials are read
from the process environment or the project .env file and are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

try:
    import requests
except ImportError as exc:
    raise SystemExit(
        "缺少 requests，请先运行：python3 -m pip install -r scripts/requirements-paddleocr.txt"
    ) from exc


DEFAULT_JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
SUPPORTED_MODELS = ("PaddleOCR-VL-1.6", "PP-OCRv6", "PP-StructureV3")


def load_dotenv(path: Path) -> Dict[str, str]:
    """Load simple KEY=VALUE pairs without overriding real environment vars."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def setting(name: str, dotenv: Dict[str, str], default: str = "") -> str:
    return os.environ.get(name, dotenv.get(name, default)).strip()


def optional_payload(model: str) -> Dict[str, bool]:
    if model == "PP-OCRv6":
        return {
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useTextlineOrientation": False,
        }
    return {
        "useDocOrientationClassify": False,
        "useDocUnwarping": False,
        "useChartRecognition": False,
    }


def response_json(response: requests.Response, label: str) -> Dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{label} 返回了非 JSON 内容（HTTP {response.status_code}）") from exc
    if response.status_code >= 400:
        message = payload.get("message") or payload.get("errorMsg") or response.text[:500]
        raise RuntimeError(f"{label} 失败（HTTP {response.status_code}）：{message}")
    return payload


def submit_job(
    session: requests.Session,
    job_url: str,
    token: str,
    model: str,
    source: str,
    timeout: int,
) -> str:
    headers = {"Authorization": f"bearer {token}"}
    payload = {"model": model, "optionalPayload": optional_payload(model)}
    if source.startswith(("http://", "https://")):
        headers["Content-Type"] = "application/json"
        response = session.post(
            job_url,
            json={"fileUrl": source, **payload},
            headers=headers,
            timeout=timeout,
        )
    else:
        input_path = Path(source).expanduser().resolve()
        if not input_path.is_file():
            raise FileNotFoundError(f"找不到输入文件：{input_path}")
        with input_path.open("rb") as handle:
            response = session.post(
                job_url,
                data={
                    "model": model,
                    "optionalPayload": json.dumps(payload["optionalPayload"]),
                },
                files={"file": (input_path.name, handle)},
                headers=headers,
                timeout=timeout,
            )
    data = response_json(response, "提交 OCR 任务").get("data", {})
    job_id = data.get("jobId")
    if not job_id:
        raise RuntimeError("提交成功但响应中没有 jobId")
    return str(job_id)


def poll_job(
    session: requests.Session,
    job_url: str,
    token: str,
    job_id: str,
    poll_seconds: int,
    timeout: int,
) -> str:
    headers = {"Authorization": f"bearer {token}"}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = session.get(f"{job_url}/{job_id}", headers=headers, timeout=timeout)
        payload = response_json(response, "查询 OCR 任务")
        data = payload.get("data", {})
        state = data.get("state")
        if state == "done":
            result_url = data.get("resultUrl", {}).get("jsonUrl")
            if result_url:
                return str(result_url)
            raise RuntimeError("OCR 任务完成但没有 jsonUrl")
        if state == "failed":
            raise RuntimeError(f"OCR 任务失败：{data.get('errorMsg', '未知错误')}")
        progress = data.get("extractProgress", {})
        total = progress.get("totalPages")
        extracted = progress.get("extractedPages")
        if total is not None and extracted is not None:
            print(f"任务状态：{state}，进度 {extracted}/{total}")
        else:
            print(f"任务状态：{state}")
        time.sleep(poll_seconds)
    raise TimeoutError(f"OCR 任务超过 {timeout} 秒仍未完成")


def safe_relative_path(value: str, fallback: str) -> Path:
    parsed = urlparse(value)
    raw = parsed.path if parsed.scheme else value
    parts = [
        re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", part)
        for part in Path(raw).parts
    ]
    clean = [part for part in parts if part not in ("", ".", "..", "/", "\\")]
    return Path(*clean) if clean else Path(fallback)


def download(session: requests.Session, url: str, target: Path, timeout: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    target.write_bytes(response.content)


def save_result_resources(
    session: requests.Session,
    result: Dict[str, Any],
    page_dir: Path,
    page_index: int,
    timeout: int,
) -> None:
    layout_results = result.get("layoutParsingResults") or []
    for item_index, item in enumerate(layout_results):
        markdown = item.get("markdown") or {}
        text = markdown.get("text") or ""
        (page_dir / f"page_{page_index:03d}_{item_index:02d}.md").write_text(
            text, encoding="utf-8"
        )
        for image_name, image_url in (markdown.get("images") or {}).items():
            target = page_dir / "markdown_images" / safe_relative_path(
                image_name, "image.bin"
            )
            download(session, str(image_url), target, timeout)
        for image_name, image_url in (item.get("outputImages") or {}).items():
            target = page_dir / "output_images" / f"{image_name}_{page_index}.jpg"
            download(session, str(image_url), target, timeout)


def save_jsonl(
    session: requests.Session,
    jsonl_url: str,
    output_dir: Path,
    timeout: int,
) -> int:
    response = session.get(jsonl_url, timeout=timeout)
    response.raise_for_status()
    lines = [line.strip() for line in response.text.splitlines() if line.strip()]
    page_count = 0
    for line_index, line in enumerate(lines):
        record = json.loads(line)
        (output_dir / f"result_{line_index:03d}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result = record.get("result") or {}
        page_dir = output_dir / f"pages_{line_index:03d}"
        save_result_resources(session, result, page_dir, line_index, timeout)
        if result.get("layoutParsingResults"):
            page_count += len(result["layoutParsingResults"])
        elif result.get("ocrResults"):
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "ocr_results.json").write_text(
                json.dumps(result["ocrResults"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            page_count += len(result["ocrResults"])
    return page_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="调用百度 AI Studio PaddleOCR API")
    parser.add_argument("source", help="本地图片/PDF路径，或可公开访问的 http(s) URL")
    parser.add_argument("--model", choices=SUPPORTED_MODELS, default=None)
    parser.add_argument("--output", default=None, help="输出目录，默认 output/paddleocr/<job_id>")
    parser.add_argument("--env-file", default=None, help="环境文件路径，默认项目根目录 .env")
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=600, help="任务总超时秒数")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    dotenv_path = Path(args.env_file).expanduser() if args.env_file else project_root / ".env"
    dotenv = load_dotenv(dotenv_path)
    token = setting("PADDLEOCR_ACCESS_TOKEN", dotenv)
    if not token:
        raise SystemExit("未找到 Token，请在项目 .env 中填写 PADDLEOCR_ACCESS_TOKEN")
    model = args.model or setting("PADDLEOCR_MODEL", dotenv, "PaddleOCR-VL-1.6")
    if model not in SUPPORTED_MODELS:
        raise SystemExit(f"不支持的模型：{model}；可选：{', '.join(SUPPORTED_MODELS)}")
    job_url = setting("PADDLEOCR_JOB_URL", dotenv, DEFAULT_JOB_URL)
    output_base = Path(
        args.output
        or setting("PADDLEOCR_OUTPUT_DIR", dotenv, str(project_root / "output" / "paddleocr"))
    )
    session = requests.Session()
    print(f"模型：{model}")
    print(f"输入：{args.source}")
    job_id = submit_job(
        session, job_url, token, model, args.source, min(args.timeout, 120)
    )
    print(f"任务已提交：{job_id}")
    jsonl_url = poll_job(
        session, job_url, token, job_id, args.poll_seconds, args.timeout
    )
    output_dir = output_base / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "job.json").write_text(
        json.dumps({"job_id": job_id, "model": model}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    page_count = save_jsonl(session, jsonl_url, output_dir, min(args.timeout, 120))
    print(f"完成：{page_count} 个页面结果，输出目录：{output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
