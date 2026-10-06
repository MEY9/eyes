# eyes：教育视觉产品工作台

这是一个面向教育视觉产品的长期仓库。第一阶段只做“教育课件 PPT 产品”，后续再扩展希沃、万彩动画和 HTML 课件。

## 当前目标

把教参、已有教学设计或微信公众号文章转换成可售卖的教育视觉产品：

```text
教参 / 教学设计 / 公众号文章
→ 内容与教学目标分析
→ PPT 故事板
→ AI 图片与视频
→ 可编辑 PPTX
→ 可选 HTML 互动环节
→ 商品演示与交付包
```

## 仓库结构

```text
agents/
  teaching-design-enhancer/    Agent A：教学设计处理
  education-ppt-pipeline/      Agent B：正式课堂 PPT 制作
  html-courseware/             Agent HTML：HTML 互动课件
skills/
  codex-ppt/                   视觉稿生成
  image-to-editable-ppt/       对象级可编辑 PPT 重建
  ppt-pipeline-catalog/        SQLite 协同目录
  ppt-animation-video/         PPT 动画视频后处理
  ppt-social-publishing/       社交平台与公众号发布包装
  read-wechat-articles/        微信公众号文章读取
products/
  education-ppt/                PPT 产品规范、SKU 与交付结构
materials/
  textbooks/                    本地教材 PDF，默认不提交远程
projects/                      具体课程项目
logs/                           任务记录、复盘和版本决策
```

## 使用方式

启动教育课件流程：

```text
/education-ppt 教参路径、教学设计路径或微信公众号链接
```

也可以分别调用：

```text
education-design-a
education-ppt-b
html-courseware
```

## 本地与远程同步原则

仓库中的 `agents/` 和 `skills/` 是源文件；ZCode 通过 `.zcode-plugin/plugin.json` 加载本项目能力。修改 Agent 或 Skill 后，先运行对应 QA，再提交并推送远程。旧的单体教育 PPT 产品 Agent、Skill 和同步脚本已经移除。

## 在 ZCode 中使用

仓库同时提供 ZCode 插件适配层：根目录 `AGENTS.md` 负责工作区协同，`.zcode-plugin/plugin.json` 是插件入口，`zcode/agents/` 提供 Agent A、Agent B 和 Agent HTML，`zcode/commands/education-ppt.md` 提供完整流程命令。

在 ZCode 中添加 GitHub 仓库 `https://github.com/MEY9/eyes` 为插件市场并安装 `eyes-education-ppt`，然后运行：

```text
/education-ppt 教参路径、教学设计路径或微信公众号链接
```

完整迁移说明见 [docs/zcode-migration.md](docs/zcode-migration.md)。

## 数据安全和版权

- 教材 PDF、客户资料、未授权图片和内部资料默认只保留在本地。
- 只有确认可以公开、商用或用于交付的素材才进入远程仓库。
- AI 生成内容要记录生成工具、日期、参考图、后处理和授权判断。
- 医学、法律和安全类内容必须保留来源和专家审核记录。
