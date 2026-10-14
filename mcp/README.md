# MCP 公开备份

本目录只保存 ZCode 与 Codex 共用的 MCP 公开事实：上游仓库、已核验版本、传输方式、端点结构、本机二进制哈希和允许的工具范围。它是 Git 中的配置索引，不是登录态备份。

权威清单为 `servers.json`。Agent 或 Skill 新增、升级或停用 MCP 时，必须在同一次变更中更新该清单和 `docs/agent-skill-dependencies.md`；用户目录里的客户端配置只是安装副本，不能反过来成为事实来源。

## 安全边界

以下内容永远不进入仓库：Cookie、token、二维码、API key、私钥、账号资料、浏览器数据、服务日志和包含时效访问令牌的响应。MCP 的登录态只保留在服务自己的本地数据目录。

## 当前服务

- `xiaohongshu-mcp`：仅供 `xhs-research` 低频只读调研。项目通过本地 Streamable HTTP 端点调用，不要求在 Codex 中注册为全局 MCP；ZCode 或 Codex 是否注册客户端连接，不改变本项目的只读工具白名单。
- OCR、生图和文档 API 继续使用项目 Python 脚本，不注册为 MCP。

## 更新流程

1. 在上游官方 Releases 核对最新稳定版本。
2. 更新本机二进制后记录版本、发布提交、文件大小、SHA-256 和核验日期。
3. 运行登录检查与一个只读搜索冒烟测试，不运行发布、点赞、收藏、评论或回复工具。
4. 更新 `servers.json`、依赖矩阵和相关 Skill；不得提交运行数据。
