# 微信公众号自动发布适配

## 采用方案

本项目不安装完整的第三方公众号 MCP 或浏览器自动化栈，而是使用官方 HTTP API 的最小适配器。GitHub 参考了：

- [white0dew/wechat-skill](https://github.com/white0dew/wechat-skill)：把“HTML 排版”和“投递公众号草稿”拆开，适合复用现有固定主题；
- [xihe-lab/wechat-mp-mcp-server](https://github.com/xihe-lab/wechat-mp-mcp-server)：覆盖官方素材上传、草稿管理、发布提交和发布状态查询；
- [obsidian-wechat-skill](https://github.com/anbulang/obsidian-wechat-skill)：记录了公众号文章内嵌视频的 `video_iframe` 兼容思路。

当前实现为项目自己的 Python 脚本 `scripts/publish_wechat_official.py`，使用 `requests` 调用官方接口，不使用 MCP，不模拟登录，不抓取 Cookie。

## 固定草稿结构

文章正文只保留两个区块：

```text
【教学设计总结内容】
教材：xxx，年级：xxx，x册，【50字以内摘要】
精研AI教育，接顶制
#标签1 #标签2 #标签3 #标签4 #标签5

【教学课件视频】
公众号视频播放器
```

脚本会把课程视频上传为公众号视频素材，然后在正文中写入带 `data-mpvid` 的公众号视频 iframe。创建草稿后必须调用 `draft/get` 回读，确认“教学课件视频”和视频 ID 仍在正文中；回读失败时禁止继续发布。

## API 链路

```text
获取 access_token
→ 上传封面永久素材 thumb
→ 上传课件视频永久素材 video
→ draft/add 创建图文草稿
→ draft/get 回读校验视频节点
→ freepublish/submit 提交发布（仅 mode=publish）
→ freepublish/get 轮询最终状态
```

草稿正文 HTML 必须使用内联 CSS；封面必须是公众号永久素材；视频必须是 MP4。官方 API 的视频素材上限按 10 MiB 预检，超过时在 Agent B 阶段先生成 `resources/wechat_video.mp4` 压缩副本，不能上传失败后把完整视频假装发布成功。正文还需满足公众号 HTML 大小和字符数限制。

## 凭据与运行模式

凭据只从当前项目 `.env` 或进程环境读取，不进入 Git、SQLite、manifest、HTML、日志或返回消息：

```text
WECHAT_MP_APPID=...
WECHAT_MP_APPSECRET=...
WECHAT_MP_PUBLISH_MODE=publish
```

`WECHAT_MP_PUBLISH_MODE=publish` 表示草稿回读校验通过后自动提交正式发布；设置为 `draft` 时只创建草稿并返回 `draft_media_id`。首次接入或权限不确定时先用 `--dry-run`，再用 `draft`，确认账号具备权限后才启用 `publish`。

脚本只打印和保存 `draft_media_id`、`publish_id`、`article_id` 和文章 URL，不打印 access token 或 AppSecret。

## 失败处理

- `40164`：检查公众号后台 IP 白名单；
- `48001`：检查账号认证状态和草稿/发布权限；
- 视频超过 10 MiB：用 FFmpeg 生成公众号专用压缩副本；
- `draft/get` 中缺少视频节点：停止，不调用 `freepublish/submit`，改走公众号后台编辑器或修复视频节点；
- 发布状态为失败、审核拒绝或超时：保留草稿 ID、发布 ID 和错误响应，登记 catalog 为 failed，不重复盲目提交。
