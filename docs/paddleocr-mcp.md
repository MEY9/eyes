# PaddleOCR MCP

## 用途

本项目通过 Codex 全局 MCP 配置接入官方 `paddleocr-mcp`，用于识别教材扫描图、微信公众号文章配图、PDF 页面和课堂素材中的文字。

当前配置：

- 运行方式：本地 CPU 推理；
- 模型：`PP-OCRv5`；
- MCP 名称：`paddleocr`；
- 传输：stdio；
- 依赖启动方式：`uvx` 自动管理 `paddleocr-mcp[local-cpu]==0.8.5`；
- 不需要百度/AI Studio 访问令牌；
- 模型缓存位于用户本机，不提交到 GitHub。

## Codex 配置

全局配置位置：

`/Users/sk/.codex/config.toml`

核心配置如下，密钥和用户凭据不写入项目：

```toml
[mcp_servers.paddleocr]
args = ["--from", "paddleocr-mcp[local-cpu]==0.8.5", "paddleocr_mcp", "--model", "PP-OCRv5", "--ppocr_source", "local"]
command = "/Users/sk/.local/bin/uvx"
startup_timeout_sec = 180

[mcp_servers.paddleocr.env]
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = "True"
```

配置修改后需要重启 Codex，新的 MCP 服务才会被加载。

## 能力边界

当前选择 `PP-OCRv5`，主要提供图像和 PDF 的文字检测与识别。需要版面结构、表格、公式、图片块或 Markdown 文档时，可在后续评估切换到官方支持的 `PP-StructureV3` 或 `PaddleOCR-VL`。

PaddleOCR MCP 不负责：

- 判断教学内容是否正确；
- 自动确认图片版权；
- 代替教师判断图片的教学作用；
- 绕过登录、验证码、访问控制或网页反爬。

## Agent A 使用约定

处理微信公众号或教材图片时：

1. 先保存原始图片来源和上下文；
2. 调用 `paddleocr` MCP 的 OCR 工具识别图片文字；
3. 将 OCR 结果与原图分开保存；
4. 对低置信度、复杂图表、手写字和艺术字标记为“需要人工核验”；
5. 不把 OCR 结果直接当成教材事实，必须结合原文和图片上下文复核。

建议产物：

```text
source_materials/wechat_original.md
source_materials/wechat_images_ocr.md
source_materials/wechat_metadata.md
```

## 安全与版本

- 不把 API Key、Access Token、Cookie、浏览器 Profile 或模型缓存提交到仓库；
- 项目只提交配置说明，不提交本机绝对路径以外的凭据；
- 版本升级前先运行 `paddleocr_mcp --help` 并完成一张图片的 OCR 回归测试；
- 如果本地 CPU 推理不可用，再评估 AI Studio、千帆或自建服务模式。

官方文档：<https://www.paddleocr.ai/latest/version3.x/integrations/mcp_server.html>
