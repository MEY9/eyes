---
name: ppt-social-publishing
description: Package Agent B's approved education PPT animation for manual publishing to Xiaohongshu, Douyin, and WeChat Channels, and create or publish a fixed-layout WeChat Official Account article containing the complete PPT slide images.
---

# 教育课件发布 Skill

## 边界

本 Skill 只负责已验收课件的发布包装与公众号投递，不负责教学设计、PPT 制作、动画规划、视频生成或内容改写。

固定分工：

- 唯一视频：产出一个 9:16 视频 `video_9x16.mp4`（1080×1920 画布，内部幻灯片保持完整 16:9），小红书、抖音、微信视频号三个平台共用这一个文件，不按平台复制。
- 小红书 / 抖音 / 微信视频号：各自生成三行 `copy.txt`，用户手动发布时都选用该唯一视频。
- 微信公众号：官方 HTTP API 创建图文草稿；正文放完整 PPT 幻灯片图片，不放课件视频。

9:16 只是视频画布比例，不是幻灯片比例。本 skill 只从 16:9 内部基底包装出这一个视频；不生成、也不允许生成任何 9:16/3:4 的幻灯片、PPT 或额外视频文件（幻灯片变竖版必然裁切或变形）。

公众号正式发布必须满足账号权限；收到 `48001` 时停止，不重复提交，不把草稿标记为已发布。

## 输入门禁

开始前必须确认：

- Agent B 已验收的完整可编辑 PPTX；
- 已验收的 16:9 视频基底（含 BGM，位于课件项目 `working/`；仅用于包装出唯一发布视频）；
- 教学设计或 `lesson_packet.json`，能够确定教材、年级、上/下册、课题和教学重点；
- 最终幻灯片图片，按 `slide_01.png` 或 `slide_01.jpg` 形式编号；
- 公众号封面图片；
- 项目 `.env` 中的 `WECHAT_MP_APPID`、`WECHAT_MP_APPSECRET`；
- `.env` 已被 Git 忽略。

缺少教材、年级、册次或教学重点时，不猜测，退回 Agent B/A。

### 固定 BGM

全线唯一指定班得瑞《雪之梦》（Snowdreams），无备选曲目，统一从原曲约 00:45 起使用至曲尾。发布包装只接收使用 `assets/bgm/snowdreams/Snowdreams_from_45s.mp3` 制作并通过 QA 的 BGM 基底；不得用旧项目残留音轨、许嵩曲库、Local Forecast 或其他音乐替代。只有本机截取段确实缺失时才登记 `awaiting_snowdreams_audio`；30 秒官方试听不能作为整条视频配乐。

## 固定发布包

在课件项目目录建立：

```text
outputs/social/
├── video_9x16.mp4
├── xiaohongshu/
│   └── copy.txt
├── douyin/
│   └── copy.txt
├── weixin_channels/
│   └── copy.txt
└── wechat_official_account/
    ├── article.html
    ├── article.md
    ├── copy.txt
    └── publish_result.json
```

## 竖版画布包装规则

整个项目唯一的发布视频 `outputs/social/video_9x16.mp4` 必须用 `scripts/package_vertical_video.py` 从 16:9 基底（`working/` 中的 BGM 版）包装生成，只改画布、不改内容，三个手动平台共用这一个文件，各平台目录内不得再放视频副本：

- 幻灯片层：完整 16:9 画面等比缩放到画布宽度（1080，高约 608），水平垂直居中；不裁切、不拉伸、不重排、不遮挡。
- 背景层：同一画面等比放大铺满 1080×1920 居中裁切后高斯模糊并压暗，仅作衬底，不承担任何信息。
- 音频照抄基底音轨（`-c:a copy`），不重编码、不替换。
- 禁止对 16:9 基底做中央裁切输出（会切掉幻灯片左右内容）；禁止非等比拉伸（会变形）；禁止在画面上添加平台装饰、进度条或字幕条。
- 不得为任何平台单独生成 9:16/3:4 幻灯片、PPT 或竖版视频母版；codex-ppt 与 image-to-editable-ppt 的工作流不因发布而重跑。

包装完成后用 ffprobe 确认 1080×1920、时长与基底一致，并抽帧检查幻灯片左右边缘内容（页眉、标题、右侧徽章）完整可见。

发布 manifest 记录源文件路径、哈希、比例、页数、时长、字体/音乐来源、排版版本和 `run_id`，不得写入 AppSecret、token 或 access_token。

## 三个平台手动文案

小红书、抖音、微信视频号的 `copy.txt` 必须是 UTF-8 三行纯文本：

```text
教材：xxx，年级：xxx，x册，【根据教学重难点和教学过程提取的50字以内摘要】
精研AI教育，接顶制
#标签1 #标签2 #标签3 #标签4 #标签5
```

摘要来自教学设计，不扩展教材没有的结论；标签必须恰好五个。括号或大括号中的用户话语是写作要求，不原样复制进文案。三个平台分别生成独立文案，但不改变三行结构。

五个标签按“学段学科 + 年级 + 教材版本 + 课型/课件 + 单元内容点”从教学设计取材，全部以 `#` 开头、单个空格分隔，不使用与课题无关的热点词。发布视频必须用 `scripts/package_vertical_video.py` 从 BGM 版 16:9 基底画布包装出唯一 `video_9x16.mp4`（9:16 画布、完整 16:9 幻灯片居中），禁止中央裁切、禁止把 16:9 原片直接上传竖版平台、禁止按平台复制视频。触发时机：语义视频 BGM 版通过 QA 后立即产出发布包，不等待用户再次指令。

## 公众号文章规则

公众号文章默认使用精品主题 `wechat-ios-showcase@1.0`。文章标题**固定格式**：`《课题》+年级上下册+科目+动态课件+AI赋能`（例：《氧化还原反应》高一第一册化学动态课件AI赋能、《秋天的雨》三年级上册语文动态课件AI赋能）；不使用悬念式营销标题，不得添加“预览”“正式课堂”等内部说明性后缀。

`wechat-ios-showcase@1.0` 当前采用壹伴“简单教育”方向的编辑部图文结构：白底、教师友好字号、暖黄色小序号、自然正文、大图展示和充足留白。禁止把文章做成 App 界面、产品详情页或数据看板，不使用深色刊头、胶囊标签、指标宫格、重复卡片、明显横线/竖线或图片描边。完整 PPT 幻灯片必须全部展示；可在其前额外选用真实 GIF 和 HTML 互动截图说明课堂用途，但仍禁止嵌入 `<video>`。底部采用双入口：公众号管理员按知识星球官方流程主动关联“知识星球”小程序、从自己星球复制小程序路径后，在草稿编辑器中把原生卡片插到二维码上方；二维码始终保留为 iOS 和异常场景回退。API 不能插入原生卡片，不使用 HTML 伪装按钮或面向读者的运营提示。旧主题仅在用户明确要求时显式选择。规范见 [references/wechat-ios-showcase.md](references/wechat-ios-showcase.md)。

正文直接从课程信息开始，不显示以下内容：

- `【教学设计总结内容】`；
- `【教学课件视频】`；
- 任何标签；
- “课件幻灯片”等制作说明；
- 技能名、平台名、内部路径或营销话术。

正文按“课程信息 → 课件简介 → AI 视频 → HTML 互动 → PPT 视觉展示 → 资料清单 → 知识星球入口”组织。课程信息必须写明教材版本、年级、上/下册和课时；文案以真实产物与课堂用途为主，不设凑字数目标，不扩写成营销文案。

文章末尾为固定转化结尾，任何课题都不得省略：小标题「END 获取完整资料」，其下一行放知识星球小程序短码 `#小程序://知识星球/AeKfWrJ03JXyNSq`（原样纯文本，不做链接化改写）。该短码是固定默认值，只有运营者另行提供新短码时才覆盖。位置在最后一张二维码图片正上方，与底部双入口（原生小程序卡片 + 二维码）叠加存在，互不替代。

公众号正文不添加品牌行。用户括号或大括号中的内容是对 Codex 的要求，必须理解后改写为自然信息，不把括号本身或指令性文字放进正文。

随后按页序插入全部 PPT 幻灯片图片。公众号正文图片必须通过 `media/uploadimg` 上传后使用返回 URL，不得直接引用本地路径、GitHub URL、CDN 或 base64。每张上传图片（含 GIF）小于 1 MiB；超限 GIF 只能生成发布专用压缩副本，不能改写已验收素材。缺图、乱序或上传失败时停止。

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
- 草稿回读必须确认教材文本和全部 PPT 幻灯片 `<img>` 节点；
- 只有 `publish_status=0` 才能标记为已发布；
- `40164` 记录为 IP 白名单问题；`48001` 记录为账号发布权限问题；
- 发布失败保留草稿 ID 和错误信息，不盲目重复提交；
- 素材硬限制：封面缩略图 ≤64 KiB（建议 900×383 JPG 压缩生成），正文插图每张 <1 MiB（建议 2560×1440 原图缩放为 1600×900 JPG）；超限先压缩再传，不降分辨率硬传；
- 草稿创建成功后先把 `draft_media_id` 落盘到 `publish_result.json`，再尝试 `freepublish`；`48001` 优雅终止并写 `draft_created_publish_unauthorized_48001`，不抛栈；
- 未认证账号 `draft/batch/get` 可能返回 `40066`，用 `draft/count` 核对草稿数量即可，不反复重试列表接口。

首次接入或权限未确认时使用 `--mode draft`。用户明确要求正式发布且权限已确认后才使用 `--mode publish`。

## QA

发布前检查：

1. 唯一发布视频 `video_9x16.mp4` 为 9:16（1080×1920）画布，由 16:9 基底包装而来：抽帧核对幻灯片区域保持完整 16:9、无裁切、无变形，背景为模糊同源画面；三个平台共用该文件，各平台目录内无视频副本；
2. 三个平台文案各三行，摘要不超过 50 个汉字，标签恰好五个；
3. 公众号文章标题固定为：《课题》+年级上下册+科目+动态课件+AI赋能（如《DNA分子的结构》高一第一册生物动态课件AI赋能）；标题之外不加品牌行或内部说明；
4. 公众号正文无标签、无视频节点、无 `【教学设计总结内容】` 和 `【教学课件视频】`；
5. 公众号文末包含固定转化结尾：小标题「END 获取完整资料」+ 短码 `#小程序://知识星球/AeKfWrJ03JXyNSq`，位于最后一张二维码图片正上方；
6. 公众号正文图片数量等于当前 PPT 实际页数；页数从当前课件的幻灯片文件或发布 manifest 枚举，顺序正确，全部来自微信 `uploadimg` URL；不得继承上一套课件的 19 页或任何固定页数；
7. 中文显示正常，无 `\\uXXXX`、`ã...` 等编码异常；
8. HTML 无外链 CSS/JS、无本地路径、无横向溢出；
9. `draft/get` 回读通过后，才允许正式发布；
10. 将结果写入 `publication_qa.md` 和 `publish_result.json`，不写入任何凭据。

详细排版与 API 约束见：

- [references/wechat-education-warm-paper.md](references/wechat-education-warm-paper.md)
- [references/wechat-ios-showcase.md](references/wechat-ios-showcase.md)
- [references/platform-spec.md](references/platform-spec.md)
- [references/wechat-auto-publish.md](references/wechat-auto-publish.md)

## 与 Agent B 的关系

```text
image-to-editable-ppt
→ PPTX 动画规划与后处理
→ ppt-animation-video（产出 16:9 内部合成基底，存于 working/）
→ ppt-social-publishing
   ├── 唯一 video_9x16.mp4 + 小红书 / 抖音 / 微信视频号各自的 copy.txt
   └── 微信公众号：完整幻灯片图文草稿或正式发布
```

公众号分支不要求视频；三个手动视频平台共用唯一 9:16 发布视频，由本 skill 从 16:9 基底包装产出。发布包完成不等于风格入库，风格入库仍等待用户确认。

## 发布后数据回流

用户手动发布到小红书后，经 `skills/xhs-research/` 拉取自己笔记的表现数据：用 `search_feeds` 搜索笔记标题（或 `user_profile` 拉账号主页），把结果写入该课件 `publish/manifest.json` 的 `performance` 字段——`{"collected_at": "ISO时间", "posts": [{"url", "title", "liked", "collected", "comments"}]}`，保留历史采集记录形成时间序列，不覆盖旧值。

规则：

- 数据回流是手动触发步骤（用户说一声拉一次），不做定时自动化；
- 只读采集，遵守 xhs-research 的低频与账号隔离约定；
- 多套课件的 performance 数据对比可反哺下一套的选题与大纲（高互动教学点优先），结论记入新立项的 `working/xhs_research.md`，不臆测因果。

## 知识星球发布节点

发布素材包到用户的知识星球（私域沉淀：动画视频 + 可编辑源文件供成员下载）。使用官方 zsxq-cli（OAuth 授权，Token 在系统钥匙串）。

### 固定配置

- 星球：`一堂微课`（group-id `48885448528888`）；更换星球时更新本节
- 认证：`zsxq-cli auth login`（OAuth 链接+确认码，用户浏览器完成）；失效时重新授权

### 发布规程

1. 写**纯文本**文案 `outputs/social/zsxq/copy.txt`：标题（课题+课时+教材版本）、摘要、资料清单（「资料包含：」+①②③④）、教材信息行。**禁止 Markdown 符号**（不用 `##`、`**`、`-` 列表符）；**不加 emoji 图标、不加品牌行**；分节用空行，列举用 ①②③；话题 ID 记入 manifest
2. **主题必须带课程封面图**：用课件封面页（slide_01）生成竖版 3:4 配图（1080×1440，幻灯片等比居中+模糊衬底），避免信息流里只露附件的 UI 文件图标；生成命令见 `scripts/make_gifs.py` 同目录说明或 ffmpeg：`scale=1080:608[main]; scale=1080:1440,boxblur=24:2[bg]; overlay 居中`
3. **附件逐文件上传，不打压缩包**：封面图（jpg，进主题图片）+ AI 导入短片（**mp4 类型不被附件接口接受，打包为同名 zip**）+ 可编辑课件 PPTX + 互动练习 HTML + 教学设计 DOCX，一次 `--files` 逗号拼接提交（编辑为全量替换，多次编辑会互相覆盖）；每附件 ≤48MB
4. **可编辑课件超 48MB 时轻量化阶梯**：解包重编码 `ppt/media`（视频 720p CRF30 逐级降 540p CRF33、图片 ≤1200px q78）直到达标；降档仍超限则改用视觉版 PPTX 替代并在正文注明
5. 发布用**纯文本**：`zsxq-cli topic +create --group-id 48885448528888 --text "$(cat copy.txt)" --files 封面图.jpg,轻量课件.pptx,互动练习.html,教学设计.docx,AI导入短片.zip`（附件上传仅 CLI 通道，MCP 不可）。**禁用 `--markdown-file`**——星球渲染器会把《课名》自动转成“查找图书”链接元素；`--text` 直传原文，换行原样保留。注意：仅 `--text` 的编辑会清空附件，附件须与文本同批或事后重挂
6. **长期授权与发布顺序**：用户已授权今后的教育课件按以下顺序执行：公众号文章正式发布成功后（`publish_status=0`）自动向“一堂微课”（group-id `48885448528888`）发布对应知识星球主题；无需逐课再次确认文案或询问是否发布。该授权不代表公众号文章本身可自动正式发布，公众号仍须遵守上文“用户明确要求正式发布”的门禁。只有公众号正式发布成功后才触发星球发布；草稿创建成功、发布失败或 `48001` 时不得提前发布星球主题。
7. 星球主题使用本 Skill 规定的纯文本格式，依据已批准的课件、教学设计和QA记录撰写，不添加未经核验的教学结论；每课只创建一次。创建前检查 `publish/manifest.json` 是否已有该课的 `zsxq.topic_id`，有则回读核实、不重复发帖；成功后立即记录 topic_id、group_id、时间、附件清单和安全的帖子链接到 manifest。用户明确要求该课提前发布时，可按该次指令执行，不改变后续默认顺序。
8. 只附带授权范围内、尺寸合规且已核验的素材。若视频音乐仅标注个人非商用且无法确认允许分发，则照常发布其他已核验附件，省略该视频，并在 manifest 记录原因；不得因缺少可选视频而停下整条已授权流程。

## iOS Showcase 文章流程（新）

公众号文章默认使用 `wechat-ios-showcase@1.0` 精品主题，流程：

1. **动图**：`scripts/make_gifs.py --video <语义视频BGM版> --segments "起-止:标签,..." [--crop w:h:x:y]`——从语义视频按时间线抽 2-4 段关键动画；发布前必须满足单张上传图片小于 1 MiB，媒体窗口片段用 `--crop w:h:x:y` 裁窗口
2. **文案**：`article.md` 用轻量标记（#TITLE/#KICKER/#SUBTITLE/#COVER/#CHIPS/##/###/>TIP/:::metrics/:::resources/![]()），钩子与亮点从教学设计重难点提取；**不得出现「定制」「知识付费」**；文末无品牌行（星球卡即出口）
3. **构建**：`scripts/build_wechat_article.py --article article.md --planet 一堂微课 --planet-qr planet_qr.png --out article.html --preview-out preview.html --theme wechat-ios-showcase@1.0`
4. **投递**：`publish_wechat_official.py --article-file article.html --asset-root <article目录> ... --mode draft`——本地图自动上传 uploadimg 并替换为微信 URL；小程序短码默认固定为 `#小程序://知识星球/AeKfWrJ03JXyNSq`（运营者另行提供时用 `--miniprogram-code` 覆盖），投递时置于文末小标题「END 获取完整资料」之下、最后一张二维码图上方，作为纯文本，不能替代后台原生卡片；只有用户明确要求正式发布且权限已确认时才改用 `--mode publish`；copy.txt 为单行课程信息格式
5. 主题规范与组件：见 `references/wechat-ios-showcase.md`。文章底部星球引流卡上方放**小程序口令文本**：`#小程序://知识星球/...` 形态（发布时原样插入、不改链接）；API 草稿不会自动转链，显示为文本——用户在编辑器中手动替换为原生小程序卡片（公众号后台需先关联知识星球小程序），构建器已在卡位预留 `WECHAT_MINIPROGRAM_INSERT` 锚点。底部收束三件套**缺一不可**：① END 章节头（卡片外白底居中：金色 END + 「获取完整资料」标题）② 小程序口令文本行（原样、不改链接）③ 官方邀请卡原图（整卡、不裁剪）；构建器 planet_card 必须按此三段输出，排版自检时逐项核对。质感规范：卡片用纸张渐变底+极浅投影+衬线标题+大数字编号+细线分隔，颜色收敛主色1+强调1+灰阶3；正文 15.5px/1.9 行距/0.3px 字距；幻灯片按教学阶段分组，使用浅色分区、页码范围和自然留白，不为每页套独立卡片
