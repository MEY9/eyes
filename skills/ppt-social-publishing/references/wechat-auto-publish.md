# 微信公众号图文自动发布适配

## 适用范围

本适配器只负责通过微信公众号官方 HTTP API 创建/发布图文文章。当前文章由两部分组成：课程摘要文字和完整 PPT 幻灯片图片。课件视频不进入公众号正文，交给微信视频号手动发布。

## 正文契约

正文可见文字只有：

```text
教材：xxx，年级：xxx，x册，根据用户话语、教学重点和教学过程提炼的摘要
精研AI教育，接顶制
```

正文不出现 `【教学设计总结内容】`、`【教学课件视频】`、标签、“课件幻灯片”、预览、正式课堂、技能名、平台名或内部路径。文章标题只使用真实课题名。

图片按 PPT 页序插入：

```html
<img src="https://mmbiz.qpic.cn/..." style="display:block;width:100%;height:auto;" />
```

图片 URL 必须来自 `media/uploadimg`，不能使用本地路径、外链 CDN、GitHub URL 或 base64。每张 JPG/PNG 必须小于 1 MiB。

## API 链路

```text
GET /cgi-bin/token
→ POST /cgi-bin/material/add_material?type=thumb
→ POST /cgi-bin/media/uploadimg（每张幻灯片一次）
→ POST /cgi-bin/draft/add
→ POST /cgi-bin/draft/get
→ 可选 POST /cgi-bin/freepublish/submit
→ 可选 POST /cgi-bin/freepublish/get
```

`draft/get` 必须验证：

- 教材信息存在；
- `精研AI教育，接顶制` 存在；
- 图片节点数等于输入幻灯片数；
- 正文没有视频节点、标签或禁止的说明性文字；
- 中文是正常字符，不是 `\\uXXXX` 或 `ã...`。

## 编码要求

微信公众号部分 API 会返回 `text/plain`，不能依赖 `response.json()` 的自动字符集推断。读取响应时优先使用：

```python
payload = json.loads(response.content.decode("utf-8"))
```

发送 JSON 时使用 UTF-8 原文：

```python
body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
requests.post(url, data=body, headers={"Content-Type": "application/json"})
```

不要把 `\\uXXXX` 转义串当作文章内容发送。

## 权限与失败

- `40164`：当前 API 出口 IP 不在公众号白名单；停止并报告微信返回的 IP。
- `48001`：账号没有对应 API 权限或认证状态不满足；草稿可保留，但不得标记为正式发布。
- `draft/get` 图片数量不一致：停止，不提交正式发布。
- 图片超过 1 MiB：先生成公众号专用压缩副本，不修改原始 PPT 图片或其他平台视频。
- 任何失败都保存无密钥的错误记录和草稿 ID，不输出 AppSecret、access_token 或请求完整 URL。
