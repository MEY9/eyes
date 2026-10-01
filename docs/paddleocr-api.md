# PaddleOCR API

本项目不使用 PaddleOCR MCP，统一通过 Python 脚本调用百度 AI Studio 的 PaddleOCR API。

## 默认模型

- `PaddleOCR-VL-1.6`：复杂图文混排、版面、表格、公式和图片型 PPT 重建；
- `PP-OCRv6`：纯文字检测、识别和文字框定位；
- `PP-StructureV3`：教材/PDF 的版面、表格、段落和阅读顺序解析。

默认使用 `PaddleOCR-VL-1.6`，可通过命令行切换。

## 配置

在项目根目录 `.env` 中填写新 Token：

```env
PADDLEOCR_ACCESS_TOKEN=你的新Token
PADDLEOCR_MODEL=PaddleOCR-VL-1.6
```

`.env` 已被 `.gitignore` 忽略，不得提交 Token、Cookie 或其他凭据。

## 使用

安装依赖：

```bash
python3 -m pip install -r scripts/requirements-paddleocr.txt
```

解析图片或 PDF：

```bash
python3 scripts/paddleocr_api.py /absolute/path/to/input.png
python3 scripts/paddleocr_api.py /absolute/path/to/input.pdf --model PP-StructureV3
python3 scripts/paddleocr_api.py /absolute/path/to/slide.png --model PP-OCRv6
```

输出默认写入 `output/paddleocr/`，包括原始 JSON、Markdown、页面结果和 API 返回的图片资源。生成目录已被 Git 忽略。

## Agent 使用约定

- Agent A 读取公众号文章图片、教材插图和截图时调用该脚本；
- `image-to-editable-ppt` 在重建页面前调用该脚本，使用 OCR 文本、文字框和版面结果辅助生成可编辑文本框；
- OCR 结果是识别证据，不是最终事实；低置信度文字、表格、公式和艺术字必须人工核验；
- 脚本不绕过登录、验证码或访问控制；
- 不在日志、提交记录或最终回复中打印 Token。

官方文档：<https://www.paddleocr.ai/latest/en/version3.x/inference_deployment/serving/paddleocr_official_api/cli.html>
