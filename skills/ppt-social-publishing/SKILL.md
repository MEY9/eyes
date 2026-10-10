---
name: ppt-social-publishing
description: Package Agent B's approved education PPT animation for manual publishing to Xiaohongshu, Douyin, and WeChat Channels, and create or publish a fixed-layout WeChat Official Account article containing the complete PPT slide images.
---

# 教育课件发布 Skill

## 边界

本 Skill 只负责已验收课件的发布包装与公众号投递，不负责教学设计、PPT 制作、动画规划、视频生成或内容改写。

固定分工：

- 小红书：生成 3:4 视频和复制文案，用户手动发布。
- 抖音：生成 9:16 视频和复制文案，用户手动发布。
- 微信视频号：生成 9:16 视频和复制文案，用户手动发布。
- 微信公众号：官方 HTTP API 创建图文草稿；正文放完整 PPT 幻灯片图片，不放课件视频。

公众号正式发布必须满足账号权限；收到 `48001` 时停止，不重复提交，不把草稿标记为已发布。

## 输入门禁

开始前必须确认：

- Agent B 已验收的完整可编辑 PPTX；
- 已验收的课件视频母版（仅用于三个手动视频平台）；
- 教学设计或 `lesson_packet.json`，能够确定教材、年级、上/下册、课题和教学重点；
- 最终幻灯片图片，按 `slide_01.png` 或 `slide_01.jpg` 形式编号；
- 公众号封面图片；
- 项目 `.env` 中的 `WECHAT_MP_APPID`、`WECHAT_MP_APPSECRET`；
- `.env` 已被 Git 忽略。

缺少教材、年级、册次或教学重点时，不猜测，退回 Agent B/A。

## 固定发布包

在课件项目目录建立：

```text
outputs/social/
├── xiaohongshu/
│   ├── video_3x4.mp4
│   └── copy.txt
├── douyin/
│   ├── video_9x16.mp4
│   └── copy.txt
├── weixin_channels/
│   ├── video_9x16.mp4
│   └── copy.txt
└── wechat_official_account/
    ├── article.html
    ├── article.md
    ├── copy.txt
    └── publish_result.json
```

发布 manifest 记录源文件路径、哈希、比例、页数、时长、字体/音乐来源、排版版本和 `run_id`，不得写入 AppSecret、token 或 access_token。

## 三个平台手动文案

小红书、抖音、微信视频号的 `copy.txt` 必须是 UTF-8 三行纯文本：

```text
教材：xxx，年级：xxx，x册，【根据教学重难点和教学过程提取的50字以内摘要】
精研AI教育，接顶制
#标签1 #标签2 #标签3 #标签4 #标签5
```

摘要来自教学设计，不扩展教材没有的结论；标签必须恰好五个。括号或大括号中的用户话语是写作要求，不原样复制进文案。三个平台分别生成独立文案，但不改变三行结构。

五个标签按“学段学科 + 年级 + 教材版本 + 课型/课件 + 单元内容点”从教学设计取材，全部以 `#` 开头、单个空格分隔，不使用与课题无关的热点词。视频包必须使用 BGM 版母版裁切（小红书 3:4、抖音/视频号 9:16 中央裁切），禁止把 16:9 原片直接上传竖版平台。触发时机：语义视频 BGM 版通过 QA 后立即产出发布包，不等待用户再次指令。

## 公众号文章规则

公众号文章使用固定主题 `wechat-education-warm-paper`，文章标题只使用真实课题名，例如 `《行路难（其一）》`，不得添加“课件幻灯片”“预览”“正式课堂”等说明性后缀。

正文直接从课程信息开始，不显示以下内容：

- `【教学设计总结内容】`；
- `【教学课件视频】`；
- 任何标签；
- “课件幻灯片”等制作说明；
- 技能名、平台名、内部路径或营销话术。

正文只包含：

```text
教材：xxx，年级：xxx，x册，根据用户话语、教学重点和教学过程提炼的摘要
精研AI教育，接顶制
```

用户括号或大括号中的内容是对 Codex 的要求，必须理解后改写为自然摘要，不把括号本身或指令性文字放进正文。

随后按页序插入全部 PPT 幻灯片图片。公众号正文图片必须通过 `media/uploadimg` 上传后使用返回 URL，不得直接引用本地路径、GitHub URL、CDN 或 base64。每张 JPG/PNG 小于 1 MiB；缺图、乱序或上传失败时停止。

公众号文章不自动上传或嵌入课件视频。视频只进入微信视频号手动发布包。

## 公众号 API 流程

必须调用 `scripts/publish_wechat_official.py`：

```text
读取 .env
→ 获取 access_token
→ 上传封面永久素材 thumb
→ 上传全部幻灯片到 media/uploadimg
→ 生成内联 CSS article.html/article.md
→ draft/add 创建图文草稿
→ draft/get 回读中文正文和全部图片数量
→ mode=publish 时才调用 freepublish/submit
→ 轮询 freepublish/get
→ 保存 publish_result.json
```

脚本要求：

- JSON 请求使用 UTF-8 原文发送，不使用会被公众号错误保存的 `\\uXXXX` 字面转义；
- API 返回即使标为 `text/plain`，也先按 UTF-8 原始字节解析；
- 不打印或保存密钥、access_token；
- 草稿回读必须确认教材文本、固定品牌句和全部 `<img>` 节点；
- 只有 `publish_status=0` 才能标记为已发布；
- `40164` 记录为 IP 白名单问题；`48001` 记录为账号发布权限问题；
- 发布失败保留草稿 ID 和错误信息，不盲目重复提交。

首次接入或权限未确认时使用 `--mode draft`。用户明确要求正式发布且权限已确认后才使用 `--mode publish`。

## QA

发布前检查：

1. 三个手动平台的视频比例正确：小红书 3:4，抖音和微信视频号 9:16；
2. 三个平台文案各三行，摘要不超过 50 个汉字，标签恰好五个；
3. 公众号文章标题只是真实课题名，无说明性后缀；
4. 公众号正文无标签、无视频节点、无 `【教学设计总结内容】` 和 `【教学课件视频】`；
5. 公众号正文图片数量等于当前 PPT 实际页数；页数从当前课件的幻灯片文件或发布 manifest 枚举，顺序正确，全部来自微信 `uploadimg` URL；不得继承上一套课件的 19 页或任何固定页数；
6. 中文显示正常，无 `\\uXXXX`、`ã...` 等编码异常；
7. HTML 无外链 CSS/JS、无本地路径、无横向溢出；
8. `draft/get` 回读通过后，才允许正式发布；
9. 将结果写入 `publication_qa.md` 和 `publish_result.json`，不写入任何凭据。

详细排版与 API 约束见：

- [references/wechat-education-warm-paper.md](references/wechat-education-warm-paper.md)
- [references/platform-spec.md](references/platform-spec.md)
- [references/wechat-auto-publish.md](references/wechat-auto-publish.md)

## 与 Agent B 的关系

```text
image-to-editable-ppt
→ PPTX 动画规划与后处理
→ ppt-animation-video（生成三个手动平台需要的视频母版）
→ ppt-social-publishing
   ├── 小红书 / 抖音 / 微信视频号：手动发布包
   └── 微信公众号：完整幻灯片图文草稿或正式发布
```

公众号分支不要求视频母版；三个手动视频平台仍要求对应比例母版。发布包完成不等于风格入库，风格入库仍等待用户确认。
