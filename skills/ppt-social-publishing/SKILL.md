---
name: ppt-social-publishing
description: Package Agent B's completed education PPT animation for Xiaohongshu, Douyin, WeChat Channels, and WeChat Official Accounts, including platform ratios, a fixed education-friendly WeChat layout, copy, tags, and auditable delivery metadata.
---

# 教育课件多平台发布包

## 定位

这是 Agent B 在 `ppt-animation-video` 完成之后调用的发布技能。它不制作教学设计、不改写 PPT 内容、不重新渲染动画，也不代替视频技能生成动画状态。它把已验收的完整课件视频和教学设计元数据整理成四个平台可直接发布的文件包。

固定平台：

| 平台 | 交付比例 | 交付物 |
|---|---|---|
| 小红书 | 3:4，1080×1440 | 完整动画 MP4、复制文案、五个标签 |
| 抖音 | 9:16，1080×1920 | 完整动画 MP4、复制文案、五个标签 |
| 微信视频号 | 9:16，1080×1920 | 完整动画 MP4、复制文案、五个标签 |
| 微信公众号 | 固定移动端文章排版 | 单文件 HTML、Markdown 备份、复制文案、五个标签 |

视频比例由本技能从已经完成的两个母版分发，不重新裁切课件主体。若某一比例缺失，退回 `ppt-animation-video`，不得用静态页面或低清截图冒充。

## 输入门禁

调用前必须存在并通过检查：

- Agent B 已确认的完整可编辑 PPTX；
- `ppt-animation-video` 已通过 QA 的 3:4 和 9:16 视频母版，或用户明确只要求其中一个平台视频；
- `lesson_packet.json`、教学设计或等价元数据，能够确定教材、年级、上/下册、教学重难点和教学过程；
- 视频没有“预览”“正式课堂”“逻辑动画版”“小红书竖屏预览”等说明性叠字；
- 同一个 `deck_id`、`style_id@version`、`catalog_db` 和发布阶段 `run_id`。

缺少教学元数据时，不猜教材、年级、册次或重难点；保留失败记录并退回 Agent B。

## 固定工作流

### 1. 建立发布包

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
    └── copy.txt
working/publication_manifest.json
working/publication_qa.md
```

发布包必须记录源视频路径、复制方式、文件哈希、画面比例、总时长、页数、字体/音乐来源、固定排版版本和生成时间。不得把 API key、token 或密码写入 manifest。

### 2. 分发视频

- 小红书只使用 3:4 母版；不得把 9:16 母版硬裁切成 3:4。
- 抖音和微信视频号只使用 9:16 母版；不得从 3:4 母版拉伸。
- 保留完整课件播放时长、封面首帧、页码、进度条、中文文字、动画顺序和背景音乐。
- 平台文件只改变容器命名和发布目录，不改变教学内容；如平台编码要求重新封装，必须在 `publication_qa.md` 记录前后规格。

### 3. 生成平台文案

每个平台单独生成一个 `copy.txt`，内容只能是以下三部分，不添加标题、引导语、表情、免责声明或额外介绍：

```text
教材：xxx，年级：xxx，x册，【根据教学重难点和教学过程提取的50字以内摘要】
精研AI教育，接顶制
#标签1 #标签2 #标签3 #标签4 #标签5
```

约束：

- 第一行教材、年级和上/下册必须来自教学设计或交接包；
- 方括号内摘要只提取本课教学重难点和教学过程，不扩展教材没有的结论，最多 50 个汉字；
- 第二行固定为“精研AI教育，接顶制”，不得改写；
- 第三行必须恰好五个中文标签，标签与本课教材、年级、知识点或 AI 课堂实践有关，不重复、不使用泛化营销词堆砌；
- 四个平台均生成独立文案文件，允许摘要和标签根据平台语境微调，但不得改变上述三行结构；
- 最终回复或交付清单中，每个平台文案都放在独立代码块内，方便复制。

### 4. 生成微信公众号固定排版

微信公众号采用固定布局 `wechat-education-warm-paper`，不是每篇文章重新选择主题。技术基线参考 GitHub 的 Markdown 转微信公众号方案：使用内联 CSS、移动端安全宽度、图片/视频资源检查和可复制 HTML；视觉上收敛为教育暖纸感，不复制项目代码。

必须阅读并遵循：

- [references/wechat-education-warm-paper.md](references/wechat-education-warm-paper.md)：固定视觉与 DOM 契约；
- [references/platform-spec.md](references/platform-spec.md)：四个平台规格、文件命名和验收字段。

HTML 要求：

- 单文件，可离线打开；CSS 内联，不依赖外部字体、JS、CDN 或远程脚本；
- 正文使用移动端安全宽度，黑色或深灰文字，留白充足，教育内容优先；
- 只保留教材、年级、册次、50 字以内摘要、固定品牌句和五个标签；
- 不出现“预览”“正式课堂”“逻辑动画版”或技能说明；
- 如果插入封面或视频缩略图，必须引用项目中已经验收的资源并记录路径；不能为了排版重新生成图片；
- HTML 与 Markdown 文本一致，HTML 预览和微信粘贴结果分别验收。

### 5. QA 和登记

检查：

1. 四个平台目录齐全，适用的视频母版存在，比例和分辨率正确；
2. 每个 `copy.txt` 只有规定的三行结构，摘要不超过 50 个汉字，标签恰好五个；
3. 微信公众号 HTML 离线打开无外链依赖，移动端正文不横向溢出；
4. 视频仍包含封面、完整页数、中文文字、页码、进度条、动画和音频流；
5. 任何平台都没有说明性叠字或不属于课件的宣传角标；
6. 生成 `publication_qa.md`，记录检查结果、失败项和修复证据。

使用 `ppt-pipeline-catalog` 为一次发布包登记 `publication_package` run、四个平台 variant、HTML/Markdown/copy/video artifact；不要把发布包状态写回 `video` run。发布包完成不等于完整课件风格入库，风格入库仍等待用户确认完整课件。

## 与 Agent B 的调用关系

Agent B 的顺序固定为：

```text
image-to-editable-ppt
→ 动画规划与 PPTX 后处理
→ ppt-animation-video（生成 3:4、9:16 母版）
→ ppt-social-publishing（四个平台发布包）
→ Agent B 最终交付与用户确认
```

Agent B 调用本技能时至少传入：可编辑 PPTX、两个视频母版、教学设计/lesson packet、项目输出目录、`deck_id`、`style_id@version`、`catalog_db` 和 `run_id`。若用户只要求某个平台，仍保留统一 manifest，但只生成被要求的平台 variant。
