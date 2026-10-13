---
name: xhs-research
description: 通过本机 xiaohongshu-mcp 服务采集小红书数据：关键词搜索帖子（含点赞/收藏/评论数）、帖子详情与图文下载、账号笔记数据回流。当课件流程需要风格参考图采集、教学素材补充、发布后数据追踪、选题调研时使用。仅限个人非商用研究用途。
---

# 小红书采集（xhs-research）

本 skill 封装本机 `xiaohongshu-mcp` 服务（HTTP 型 MCP，端口 18060），为课件流水线提供三类数据：风格参考图、教学素材、发布后表现数据。

## 服务管理

- 程序位置：`E:\tools\xiaohongshu-mcp\xiaohongshu-mcp.exe`（v2.5.5）
- 启动：在该目录运行 `xiaohongshu-mcp.exe`（后台），日志写 `service.log`；首次启动自动下载内置浏览器（仅一次）
- 端点：`http://localhost:18060/mcp`（Streamable HTTP，JSON-RPC）
- 登录：cookie 保存在服务数据目录，长期有效；**检查登录失败即为阻断点**——调 `get_login_qrcode` 取码、存盘后请用户用小红书 App 扫码（约 3 分钟有效期，过期重新生成），完成后 `check_login_status` 复核
- 注意：同一小红书账号不要在其他网页端同时登录，会被踢出

## 调用规范（必须遵守）

1. **一律用 Python `requests` 直调**，JSON 体内含中文；**禁止用 curl/shell 内联中文参数**——Git Bash 会把 UTF-8 搞坏（实测踩坑：搜"高中生物课件"因编码损坏返回无关结果）
2. 每次调用间隔 ≥3 秒，低频使用；本项目默认**只读**
3. 调用方示意见 `scripts/xhs_call.py`，优先用它而不是现写请求

```python
import requests
payload = {"jsonrpc":"2.0","id":1,"method":"tools/call",
           "params":{"name":"search_feeds","arguments":{"keyword":"高中生物课件"}}}
r = requests.post("http://localhost:18060/mcp", json=payload, timeout=120)
text = r.json()["result"]["content"][0]["text"]   # JSON 字符串，再 json.loads 一次
```

## 工具清单（本项目允许范围——只读）

| 工具 | 用途 |
|---|---|
| `check_login_status` | 登录检查（每次采集会话开始时调用） |
| `get_login_qrcode` | 扫码登录（仅阻断点使用） |
| `search_feeds` | 关键词搜索，返回帖子列表含 `interactInfo`（likedCount/collectedCount/commentCount/sharedCount）、封面、作者 |
| `get_feed_detail` | 帖子详情：完整正文、话题标签、`imageList`、评论列表；需 `feed_id` + `xsec_token`（搜索结果里带） |
| `user_profile` | 账号主页笔记列表（发布后数据追踪用） |

**禁用工具**：`publish_content`、`publish_with_video`、`like_feed`、`favorite_feed`、`post_comment_to_feed`、`reply_comment_in_feed`、`reply_notification`——本项目一律不使用自动写操作；发布走 ppt-social-publishing 的手动包流程。

## 用例一：风格参考图采集（Agent B 风格候选阶段，P0）

1. 关键词模板：`{课题} 课件`、`公开课课件 {学段学科}`、`PPT 设计 教育`、`教学 KV`；取互动数最高的帖子
2. 下载封面/内页图到 `style_candidates/reference-xhs/`
3. 同目录写 `provenance.json`：每张图记 `{帖子URL, 标题, 作者, 点赞/收藏数, 采集时间}`
4. 提炼视觉 DNA 时**只取配色、图形语言、版式三项**；参考图中的品牌 logo、水印、原帖文字一律不进课件
5. 风格候选仍走用户确认门；用户自带参考图时以用户为准，采集仅作补充

## 用例二：教学素材补充（Agent A 教学设计阶段）

1. 博查做通用检索；同课题的小红书教师帖（课件、教学反思、学情讨论）作为补充素材源
2. 高赞帖的点赞/收藏数作为素材质量信号；详情正文与图片存 `source_materials/xhs/`
3. 来源（URL、作者、互动数据、采集时间）记入 `working/source_audit.md`

## 用例三：发布后数据回流（ppt-social-publishing）

1. 用户手动发布后，用 `search_feeds`（搜自己笔记标题）或 `user_profile` 拉自己笔记数据
2. 写入该课件 `publish/manifest.json` 的 `performance` 字段：`{"collected_at": ..., "posts": [{"url","title","liked","collected","comments"}]}`
3. 多次采集自然形成时间序列；对比多套课件数据可反哺选题

## 用例四：选题调研（Agent B 立项，可选）

搜同课题高互动教学点与课件需求帖（"求课件""怎么讲"类），产出 `working/xhs_research.md`：高互动教学情境、教师痛点、风格偏好。素材已充分时可跳过本步。

## 输出与登记

- 采集结果 JSON、图片一律落盘到调用方指定的项目目录，不留在服务目录
- 每次采集会话在 catalog 登记 run（来源 URL、数据快照时间、产物哈希），无密钥
- `xsec_token` 是时效性访问令牌，随搜索结果返回、随详情请求使用，不落 Git
