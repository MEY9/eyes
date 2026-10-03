# 多平台发布规格

## 平台映射

| platform | output_ratio | canvas | source_master | required_files |
|---|---|---|---|---|
| xiaohongshu | 3:4 | 1080×1440 | 3:4 MP4 | `video_3x4.mp4`, `copy.txt` |
| douyin | 9:16 | 1080×1920 | 9:16 MP4 | `video_9x16.mp4`, `copy.txt` |
| weixin_channels | 9:16 | 1080×1920 | 9:16 MP4 | `video_9x16.mp4`, `copy.txt` |
| wechat_official_account | article | mobile-safe | teaching metadata + all PPT slide images | `article.html`, `article.md`, `copy.txt`, `publish_result.json` |

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

小红书、抖音、微信视频号复制文件必须是 UTF-8 纯文本三行：教材/年级/册次/摘要、固定品牌句、五个标签。微信公众号复制文件为 UTF-8 纯文本两行：教材/年级/册次/根据用户话语和教学设计提炼的摘要、固定品牌句；不输出标签。用户在括号或大括号中的话是写作要求，不原样复制。

公众号文章标题只使用真实课题名；正文不添加说明性区块标题。正文幻灯片数量必须等于 PPT 页数，图片顺序按页码排列，单张 JPG/PNG 小于 1 MiB，并使用 `media/uploadimg` 返回的微信图片 URL。
