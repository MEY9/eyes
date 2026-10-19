# Backend Selection

Read this before confirming the image backend or generating the representative sample set.

## Backends

1. **API/CLI backend — default.** Uses `scripts/image_gen.py` against the OpenAI-compatible endpoint configured in the project-level `.env`.
2. **Codex OAuth / built-in image tool — disabled by default.** The CLI treats `CODEX_PPT_DISABLE_CODEX_OAUTH` as `1` unless the user exports `CODEX_PPT_DISABLE_CODEX_OAUTH=0`, so `~/.codex/auth.json` is never read and no job is routed through the ChatGPT/Codex image endpoints.

## Configuration Precedence

Highest first:

1. Process environment variables
2. Project-level `.env` — found by walking up from the current working directory and stopping after the directory that contains `.git`; nearer files override farther ones. Override the search with `CODEX_PPT_PROJECT_ENV=<path>`.
3. Global `~/.codex-ppt-skill/.env`
4. Built-in defaults

Relevant keys: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `CODEX_PPT_IMAGE_MODEL`.

## Decision Rules

- Default to the API/CLI backend. Do not switch to Codex OAuth or the built-in image tool unless the user explicitly exports `CODEX_PPT_DISABLE_CODEX_OAUTH=0`.
- Do not describe the API/CLI backend as a "fallback". It is the configured primary path for this project.
- Do not identify the endpoint as a specific GPT Image model unless the configuration provides evidence. If exact model, size, or quality selection is required but the provider does not expose it, explain the limitation and confirm the setting with the user.
- Before generating the first image, tell the user which `.env` file was resolved, which backend you plan to use, and confirm the endpoint and model. Wait for confirmation.
- Configure credentials with `scripts/codex_ppt_runtime.py config --api-key`. Never copy credentials, tokens, or `.env` contents into prompts, manifests, logs, or generated artifacts.

If CLI/API fallback is selected, read `cli-api-fallback.md` before generating images. For API key, base URL, model, and `.env` configuration, read `image-model-configuration.md` only after the fallback CLI reports missing or invalid configuration, or when the user explicitly wants to change those settings.

## Confirmation Text

```text
我已解析到项目级 .env（<解析到的 .env 路径>），准备使用 API/CLI 图片后端生成三组候选风格样稿：端点 <OPENAI_BASE_URL>、模型 <CODEX_PPT_IMAGE_MODEL>，Codex OAuth 已按项目约定禁用。每组包含封面/导入、普通讲授、活动/练习页各一张，分别打包为风格1.pdf、风格2.pdf、风格3.pdf。可以开始生成三组样稿吗？
```

Wait for confirmation before generating the representative sample set. If the user questions the backend, resolve that before continuing.
