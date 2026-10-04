# 在 ZCode 中使用 eyes 教育课件系统

本仓库已经包含一个 ZCode 插件适配层，插件入口是 `.zcode-plugin/plugin.json`，工作区规则是根目录 `AGENTS.md`，三个专用 Agent 位于 `zcode/agents/`，完整业务规范仍以 `agents/` 和 `skills/` 中的源文件为准。

## 安装方式

1. 在 ZCode 中打开本仓库目录：`/Users/sk/Documents/Codex/monigouwu/eyes`。
2. 在 Settings → Plugins 中添加 GitHub 插件市场，地址填写：`https://github.com/MEY9/eyes`；刷新后安装 `eyes-education-ppt`。
3. 如果只想本地试用，也可以把当前仓库根目录作为本地插件目录添加。插件根目录必须能看到 `.zcode-plugin/plugin.json`。
4. 重新打开工作区，确认 `/education-ppt` 命令、`agent-a`、`agent-b` 和 `agent-html` 可见。

ZCode 也支持从 Codex CLI 导入 Skill。若插件市场暂时未刷新，可在 Settings → Skills → Import 中导入项目的 `skills/` 子目录；优先选择复制到当前项目，长期使用再选择全局安装。复制或软链接后仍要让 ZCode 在当前工作区读取根目录 `AGENTS.md`。

## 标准使用

在 ZCode 中输入：

```text
/education-ppt https://mp.weixin.qq.com/s/文章链接
```

也可以输入教材或教学设计文件路径。流程不会把公众号文章直接变成 PPT，而是先生成教学设计 Word 文档，再生成课件大纲、视觉稿、对象级可编辑 PPTX，最后按要求做 HTML、动画、视频和公众号发布。

## 环境与安全

项目使用 Python API 脚本处理 OCR 和外部生图/文档接口，不默认启用 MCP。API key、OCR token、公众号凭证等写在项目根目录 `.env`，该文件已被 Git 忽略；不要把密钥粘贴进 Agent、Skill、日志、SQLite 或交接 JSON。

HTML 运行检查需要浏览器时，在 ZCode 中启用 Browser Use；这不是 MCP，也不改变 HTML 单文件和静态备用要求。SQLite catalog 仍由 `ppt-pipeline-catalog` 负责记录 deck、style、run、artifact 和审批关系，项目文件与 Git 仍是唯一事实来源。

## 验收清单

- Agent A 交付 Word 教学设计、`lesson_packet.json`、来源审计和 AI 任务状态。
- 必需 AI 任务已产生真实资源并通过门禁；只有提示词不算完成。
- Agent B 交付实际页数的完整课堂 PPT，页数不固定为 19 页。
- codex-ppt 先锁定风格；image-to-editable-ppt 将所有可识别元素拆为可编辑对象。
- HTML 有单文件、预览、静态备用和运行检查；动画按教学逻辑组织。
- 公众号文章只按当前发布 Skill 生成固定版式和完整幻灯片内容，其他平台保持手动发布包装。
