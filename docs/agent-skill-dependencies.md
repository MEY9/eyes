# 多 Agent 与 Skill 依赖矩阵

本文件记录教育课件生产系统的真实调用关系。`AGENTS.md` 负责跨 Agent 编排，`agents/*/AGENT.md` 和 `skills/*/SKILL.md` 负责各自详细契约；本文件只回答“哪个 Agent 在什么条件下需要哪个 Skill”，用于 ZCode/Codex 按需加载、安装检查和清理。

## 固定协同链路

```text
来源归档
→ Agent A：教学设计与 lesson_packet.json
→ AI 赋能任务执行
→ Agent HTML（仅 HTML 任务）
→ Agent B：大纲、3×3 风格样稿、正式视觉稿
→ 对象级可编辑重建
→ 可选配音、动画视频与发布包装
```

所有阶段沿用同一 `deck_id`；视觉阶段沿用同一 `style_id@version`；每次运行使用独立 `run_id`。项目文件和 Git 是事实来源，SQLite catalog 只记录索引、状态、哈希和审批关系。

## Agent 依赖

| 调用者 | Skill / 能力 | 条件 | 产物或作用 |
|---|---|---|---|
| Agent A | `ppt-pipeline-catalog` | 建立或继续项目时 | 登记统一 `deck_id`、教学设计 run 与交接 artifact |
| Agent A | `read-wechat-articles` | 输入是公开微信公众号链接时 | 读取正文 JSON，由 A 归档到 `source_materials/` |
| Agent A | 文档生成与渲染能力 | 生成正式教学设计时 | 黑色五号宋体 DOCX、渲染预览与格式 QA；属于运行环境能力，不在本仓库重复维护 Skill 副本 |
| Agent HTML | `ppt-pipeline-catalog` | 项目启用 catalog 时 | 登记独立 HTML run 与交互产物 |
| Agent HTML | 浏览器运行检查能力 | 存在 HTML 赋能任务时 | 离线交互、反馈、重置、中文显示和静态备用 QA；不作为项目 MCP 备份 |
| Agent B | `ppt-pipeline-catalog` | 全流程必需 | 编排阶段、artifact、审批和风格状态 |
| Agent B | `xhs-research` | 风格候选阶段；素材补充/立项调研按需 | 只读采集参考图、教学素材和互动数据 |
| Agent B | `codex-ppt` | 大纲与 3×3 风格确认后 | 生成正式视觉稿与视觉版 PPTX |
| Agent B | `image-to-editable-ppt` | 视觉稿 QA 通过后 | 完全拆解并重建对象级可编辑 PPTX |
| Agent B | `azure-tts` | 用户或教学设计明确需要课件旁白时 | 生成课件旁白；不处理 AI 视频内部声音 |
| Agent B | `ppt-animation-video` | 用户需要连续课件视频时 | 从可编辑 PPTX 和语义动画清单生成 16:9 内部基底 |
| Agent B | `ppt-social-publishing` | 视频发布包装/公众号投递被启用时 | 唯一 9:16 发布视频、三平台文案、公众号图文草稿/发布结果 |

## 安装分类

### 生产链 Skill

仓库把以下八项作为生产能力的权威源码；这不等于每台客户端都要复制安装八份。ZCode 插件可以从本仓库暴露它们，Codex 只在当前任务实际触发时读取或安装对应项；具体运行仍按条件触发：

1. `read-wechat-articles`
2. `ppt-pipeline-catalog`
3. `xhs-research`
4. `codex-ppt`
5. `image-to-editable-ppt`
6. `azure-tts`
7. `ppt-animation-video`
8. `ppt-social-publishing`

### 独立工具，不随生产链加载

- `github-link-collector`：只在用户明确要求收藏 GitHub 项目时使用；不属于 A→HTML→B 课件生产链。

### 已删除的废弃能力

- `gpt-image2-ppt`：旧的单体生图 PPT Skill，已由 `codex-ppt` 加 `image-to-editable-ppt` 的两阶段路线替代。当前工作树和 ZCode 安装副本均不保留；Git 历史可恢复，但恢复必须取得用户明确授权。

## 外部运行依赖

- PaddleOCR：通过 `scripts/paddleocr_api.py`，不默认注册为 MCP。
- 小红书：`xhs-research` 通过本机 `xiaohongshu-mcp` 的只读 HTTP 端点调用；无密钥版本、端点、二进制哈希和工具白名单保存在 `mcp/servers.json`。
- 图片生成：优先项目 `.env` 指定的 OpenAI 兼容图像接口；额度或能力不可用时按 Agent B 契约回落。
- AI 视频：只使用 Agent B 规定的即梦模型与次数门禁。
- 知识星球：发布节点使用官方 `zsxq-cli`，认证保存在系统安全存储，不进入仓库。

## 双端切换规则

1. ZCode 和 Codex 使用同一仓库、同一 `origin`、同一分支事实。
2. Agent/Skill 规范先改仓库权威源，不先改用户目录安装副本。
3. 同一具体 `project/` 子目录不能被两端同时写入；切换前停止运行并保存 `pipeline_state.json`、catalog 快照和 QA 证据。
4. 独立项目可以分别由两端开发，但不得共享同一 `deck_id` 或互相覆盖运行目录。
5. `.env`、MCP Cookie/token、账号凭据、SQLite 运行库和私密客户材料不提交 Git。
6. 切换客户端或升级 Agent、Skill、MCP 后运行 `python scripts/verify_workspace_contract.py`；校验失败时先修复仓库权威源，不用旧的用户目录副本覆盖仓库。
