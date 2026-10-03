---
name: read-wechat-articles
description: Read public articles hosted on https://mp.weixin.qq.com, extracting the title, author, publication time,正文, and image URLs directly into Codex without creating Markdown or other intermediate files. Use when a user provides a WeChat Official Account article URL or asks Codex to read, summarize, analyze, quote, or answer questions about an mp.weixin.qq.com article.
---

# Read WeChat Articles

Use the bundled standard-library Python script to fetch and parse each public article:

```powershell
python "<skill-directory>\scripts\read_article.py" "https://mp.weixin.qq.com/s/..."
```

Replace `<skill-directory>` with the directory containing this `SKILL.md`. The script writes no files and emits one UTF-8 JSON document to stdout with `title`, `author`, `published_at`, `url`, `content`, and `images`.

Read the JSON output and answer the user's requested question or produce the requested summary. Treat `content` as the article正文 and use `images` only when visual material is relevant. Do not reproduce the full article unless the user's request and applicable copyright rules allow it.

Run the script once per URL when several articles are supplied. If it exits unsuccessfully or reports that the正文 is missing, explain that the page may require verification or that WeChat's page structure may have changed; do not invent missing content.
