# 多平台发布规格

## 平台映射

整个项目只交付一个视频文件：`outputs/social/video_9x16.mp4`，三个手动平台共用，各平台目录只放 `copy.txt`。`output_ratio` 指视频画布比例，幻灯片内容在画布中始终保持完整 16:9（见下文"竖版画布适配"）。

| platform | output_ratio | canvas | slide_region | required_files |
|---|---|---|---|---|
| xiaohongshu | 9:16 | 1080×1920 | 完整 16:9 居中 | `copy.txt`（共用 `../video_9x16.mp4`） |
| douyin | 9:16 | 1080×1920 | 完整 16:9 居中 | `copy.txt`（共用 `../video_9x16.mp4`） |
| weixin_channels | 9:16 | 1080×1920 | 完整 16:9 居中 | `copy.txt`（共用 `../video_9x16.mp4`） |
| wechat_official_account | article | mobile-safe | — | `article.html`, `article.md`, `copy.txt`, `publish_result.json` |

全项目不得出现 3:4（1080×1440）版本、按平台复制的视频副本，或 3:4/9:16 多母版——视频基底只有一个 16:9（内部产物，存于 `working/`），对外交付的视频只有一个 9:16。

## 竖版画布适配

9:16 只是视频画布比例，幻灯片比例不变。唯一允许的适配方式（从 `working/` 中的 16:9 BGM 基底包装出唯一的 `outputs/social/video_9x16.mp4`）：

1. 幻灯片层：完整 16:9 基底画面等比缩放到画布宽度 1080（高约 608，取偶数），水平垂直居中。
2. 背景层：同一画面等比放大铺满 1080×1920 并居中裁切，高斯模糊（默认 `gblur=sigma=28`）后压暗（默认 `eq=brightness=-0.08`），仅作衬底。
3. 音频照抄基底音轨（`-c:a copy`）。

必须调用 `scripts/package_vertical_video.py` 完成包装（内部即下述命令），等价 FFmpeg 命令：

```bash
ffmpeg -i master_16x9.mp4 -filter_complex \
"[0:v]split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.08[bgb];\
[fg]scale=1080:608[fgs];\
[bgb][fgs]overlay=(W-w)/2:(H-h)/2" \
-c:a copy -movflags +faststart output_9x16.mp4
```

硬性禁止：

- 禁止对 16:9 基底做中央裁切产出竖版（会切掉幻灯片左右内容）；
- 禁止非等比拉伸（幻灯片变形）；
- 禁止为平台重新生成 9:16/3:4 幻灯片、PPT 或任何额外视频文件（包括按平台复制的视频副本）；
- 禁止在画面上添加平台装饰、进度条、字幕条。

包装后校验：ffprobe 确认 1080×1920、时长与基底一致；抽帧核对幻灯片左右边缘内容（页眉、标题、右侧徽章等）完整可见。

## publication_manifest.json

```json
{
  "deck_id": "...",
  "style_key": "...",
  "package_id": "...",
  "layout_id": "wechat-ios-showcase@1.0",
  "release_video": {
    "path": "outputs/social/video_9x16.mp4",
    "sha256": "...",
    "canvas": "1080x1920",
    "slide_region": "16:9 centered, blur-pad background",
    "source_base": {"ratio": "16:9", "path": "working/...", "sha256": "..."}
  },
  "variants": [
    {
      "platform": "xiaohongshu",
      "ratio": "9:16",
      "video_path": "outputs/social/video_9x16.mp4",
      "copy_path": "outputs/social/xiaohongshu/copy.txt",
      "tags": ["...", "...", "...", "...", "..."]
    }
  ]
}
```

`variants` 中三个手动平台的 `ratio` 均为 `9:16`，`video_path` 全部指向同一个 `outputs/social/video_9x16.mp4`；manifest 不得写入 AppSecret、token 或 access_token。

## 文案硬约束

小红书、抖音、微信视频号复制文件必须是 UTF-8 纯文本三行：教材/年级/册次/摘要、固定品牌句、五个标签。微信公众号复制文件为 UTF-8 纯文本一行，只写教材/年级/册次/根据用户话语和教学设计提炼的摘要；不写品牌行和标签。用户在括号或大括号中的话是写作要求，不原样复制。

公众号文章标题只使用用户确认的真实课程信息，不固定添加“AI赋能”等宣传尾缀；正文按课程信息、简介、真实 AI 资源、PPT 展示、资料入口组织，不添加品牌行。正文幻灯片数量必须等于 PPT 页数，图片顺序按页码排列，单张上传图片（含 GIF）小于 1 MiB，并使用 `media/uploadimg` 返回的微信图片 URL。PPT 长画廊按教学阶段分组，不能为每张幻灯片添加独立圆角卡、描边或投影。
