# 微信公众号固定排版：wechat-education-warm-paper

## 选型依据

本项目采用固定的教育暖纸感主题。技术实现借鉴 [leapx-ai/Markdown-to-WeChat](https://github.com/leapx-ai/Markdown-to-WeChat) 的 Markdown 转微信公众号、内联 CSS 和多主题思路；图片/资源检查可参考 [leether/md2wechat](https://github.com/leether/md2wechat) 的发布前处理方式。GitHub 项目只作为技术和排版参考，当前主题是本项目自己的固定适配层。

## 视觉契约

- 页面宽度以 680px 为设计基准，正文在手机上保持左右安全边距；
- 背景使用暖白 `#FBF8F2`，内容卡片使用 `#FFFFFF`，正文使用近黑 `#20252B`；
- 主强调色使用低饱和青绿 `#5C8D83`，次强调色使用教育暖黄 `#D7A64A`；
- 标题使用清晰的黑色或深灰系统中文字体，不使用艺术字、渐变字、描边字或依赖外部字体；
- 采用细分隔线、圆角信息卡、轻量标签和充足留白，不使用强营销海报、复杂装饰、闪烁动画或大面积渐变；
- 摘要、品牌句和标签作为正文内容，不额外增加“点击查看”“预览”“爆款”等营销语。

## 固定 DOM 顺序

```text
article
└── header.course-meta
    ├── p.subject-line       教材、年级、册次
    ├── h1.lesson-summary    50字以内摘要
    └── p.brand-line         精研AI教育，接顶制
└── section.tags
    └── span.tag × 5
└── figure.cover             可选，使用已验收封面资源
└── footer.source-note       可选，仅在用户明确需要时显示来源
```

当前用户要求“文案只写”时，省略 `cover` 和 `source-note`，只输出 `course-meta` 与 `tags`。不得把 PPT 制作说明、技能名、平台名或内部路径渲染到文章中。

## HTML 实现要求

- 只使用内联 CSS 和 HTML，不依赖 CDN、外部脚本或远程字体；
- HTML、Markdown 和 `copy.txt` 的可见文案逐字一致；
- 用 `overflow-wrap:anywhere`、合理的 `line-height` 和安全边距避免长标签横向溢出；
- 输出前用浏览器或等效渲染器检查手机宽度，确认没有滚动条、裁切、乱码和空白媒体框；
- 固定布局的版本写入 manifest，例如 `wechat-education-warm-paper@1.0`，后续只通过版本升级改变，不在单篇文章中私自换主题。
