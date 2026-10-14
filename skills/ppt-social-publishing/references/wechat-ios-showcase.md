# wechat-ios-showcase@1.0

## 定位

`wechat-ios-showcase@1.0` 是微信公众号教育案例的精品展示主题。它借鉴 iOS 的信息层级、分组卡片、系统蓝强调色与充足留白，但不照搬手机界面，也不依赖公众号编辑器容易丢失的复杂 CSS。

该主题是显式启用的独立主题，不替换默认 `wechat-education-warm-paper`。只有用户明确选择精品展示风格时，才可在构建命令中传入：

```powershell
python skills/ppt-social-publishing/scripts/build_wechat_article.py `
  --theme wechat-ios-showcase@1.0 `
  --article <article.md> `
  --planet "一堂微课" `
  --planet-qr <qr.png> `
  --out <article_ios_showcase.html>
```

## 视觉原则

- 内容优先：正文保持 15px、约 1.9 倍行高，标题不超过 24px。
- 单一强调色：系统蓝 `#007AFF` 只用于章节标识、重点和小标签。
- 分组而不堆卡：正文自然排版，媒体、指标、资料包和引流区使用浅灰分组容器。
- 克制圆角：主要容器 18–20px，图片内框 13–14px，胶囊仅用于短标签。
- 不使用投影、渐变、玻璃拟态或模拟 iPhone 外壳。
- 素材风格统一；GIF 只承担“过程变化”的演示，不作为装饰。

## 固定结构

1. 刊头：教材信息、主标题、蓝色短线、副标题、内容标签。
2. 导语：提出教师真实痛点与文章价值。
3. 章节：使用 `CHAPTER 01` 等小型序号建立阅读进度。
4. 媒体卡：课件实景或动态演示、简短图注、观看重点。
5. 指标条：使用四列表格，不使用 CSS Grid。
6. 资料包：分组清单，名称与文件信息分层展示。
7. 转化区：原生小程序卡片插入锚点、二维码回退入口、品牌落款。

## 知识星球小程序

HTML 不伪装小程序按钮。主题在转化区写入唯一注释锚点：

```html
<!-- WECHAT_MINIPROGRAM_INSERT: 在此插入知识星球原生小程序卡片；保留下方二维码作为回退入口 -->
```

公众号 API 创建草稿后，由运营者在微信后台打开草稿，在该锚点对应的可见提示卡上方插入知识星球原生小程序卡片。二维码必须保留，作为小程序卡片未显示或用户无法进入时的回退路径。

## 兼容边界

- 所有样式必须内联。
- 禁止 `<style>`、`class`、`id`、CSS 变量、脚本、表单、iframe、SVG、Canvas、音视频节点。
- 不使用 Grid、复杂 Flex、固定定位、粘性定位、媒体查询和 `gap`。
- 横向指标仅使用 `<table>`。
- 正文图片必须包含 `max-width:100%;height:auto;display:block;`。
- 正文图片发布前必须上传到微信并替换为 `media/uploadimg` 返回地址。
- 发布前在 iPhone 浅色与深色模式各预览一次，并核对小程序卡片、二维码、GIF 首帧与全文顺序。

## 验收证据

- 输出 HTML、预览 HTML、素材清单和主题元数据。
- 主题元数据中的 `theme_id` 必须等于 `wechat-ios-showcase@1.0`。
- `WECHAT_MINIPROGRAM_INSERT` 锚点只能出现一次。
- 所有本地素材存在，图片顺序与源文一致。
- 禁用标签、禁用 CSS 与敏感占位内容扫描为零。
