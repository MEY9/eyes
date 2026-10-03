# 多平台发布规格

## 平台映射

| platform | output_ratio | canvas | source_master | required_files |
|---|---|---|---|---|
| xiaohongshu | 3:4 | 1080×1440 | 3:4 MP4 | `video_3x4.mp4`, `copy.txt` |
| douyin | 9:16 | 1080×1920 | 9:16 MP4 | `video_9x16.mp4`, `copy.txt` |
| weixin_channels | 9:16 | 1080×1920 | 9:16 MP4 | `video_9x16.mp4`, `copy.txt` |
| wechat_official_account | article | mobile-safe | teaching metadata | `article.html`, `article.md`, `copy.txt` |

## publication_manifest.json

```json
{
  "deck_id": "...",
  "style_key": "...",
  "package_id": "...",
  "layout_id": "wechat-education-warm-paper@1.0",
  "source_masters": {
    "3:4": {"path": "...", "sha256": "..."},
    "9:16": {"path": "...", "sha256": "..."}
  },
  "variants": [
    {
      "platform": "xiaohongshu",
      "ratio": "3:4",
      "video_path": "...",
      "copy_path": "...",
      "tags": ["...", "...", "...", "...", "..."]
    }
  ]
}
```

## 文案硬约束

复制文件必须是 UTF-8 纯文本，且只有三行：教材/年级/册次/摘要、固定品牌句、五个标签。摘要按 Python 的 Unicode 字符计数，不能超过 50 个汉字；标签数组和显示文本都必须恰好五个。
