# Read WeChat Articles

让 Codex 直接读取微信公众号公开文章，并根据正文进行总结、分析和问答。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

解决 Codex 不读取微信公众号文章的问题。无需浏览器自动化、登录或 API Key。安装后通常只需把文章链接交给 Codex，不必手动运行 Python 脚本，也不会生成 Markdown 等中间文件。

## 快速开始

### 安装

将下面这句话发送给 Codex：

```text
使用 $skill-installer 从 XUMUMI/read-wechat-articles 仓库根目录安装 Skill，名称为 read-wechat-articles。
```

安装后如果 Skill 没有立即出现，请重启 Codex。

## 能做什么

- 提取文章标题、作者、发布时间、正文和图片链接
- 总结全文或指定章节
- 整理核心观点、关键数据和行动项
- 对多篇文章进行比较
- 根据文章内容回答具体问题

安装后，Codex 也可以在任务与 Skill 描述匹配时自动调用它。

## 其他安装方式

使用跨 Agent 的 Skills CLI：

```bash
npx skills add XUMUMI/read-wechat-articles -g -a codex
```

## 兼容性与环境要求

- 需要能够访问 `mp.weixin.qq.com` 和文章图片域名
- 目标文章必须无需登录即可公开访问

其他 Codex 客户端和操作系统理论上可以使用，但目前尚未逐一验证。

## 隐私与限制

- 脚本仅请求用户提供的微信公众号公开文章，不使用 Cookie 或账号凭据
- 解析结果通过标准输出交给 Codex，不写入本地文件
- 如果微信要求验证码、登录或其他人工验证，读取会失败
- 微信修改页面结构后，解析规则可能需要同步更新
- 图片只返回原始链接，不执行 OCR 或图像内容分析
- 已删除、仅粉丝可见或其他受限文章无法读取

<details>
<summary><strong>技术细节</strong></summary>

### 输出格式

[`scripts/read_article.py`](scripts/read_article.py) 会向标准输出写入 UTF-8 JSON：

```json
{
  "title": "文章标题",
  "author": "公众号名称",
  "published_at": "2026-08-07T21:56+08:00",
  "url": "https://mp.weixin.qq.com/s/...",
  "content": "文章正文……",
  "images": [
    "https://mmbiz.qpic.cn/..."
  ]
}
```

### 工作原理

脚本使用接近普通浏览器的请求头下载公开页面，再从微信文章的 HTML 结构中提取元数据和正文。它最多读取 8 MiB，只接受 HTTPS 的 `mp.weixin.qq.com` URL。

### 项目结构

```text
read-wechat-articles/
├── SKILL.md                 # Skill 触发条件与执行说明
├── LICENSE                  # MIT 许可证
├── agents/
│   └── openai.yaml         # Codex UI 元数据
└── scripts/
    └── read_article.py     # 微信文章下载与解析脚本
```

</details>

## 许可证

本项目采用 [MIT License](LICENSE)。你可以自由使用、复制、修改和分发本项目，也可以用于商业用途；分发副本或重要修改时需要保留原版权声明和许可证文本。本项目按“原样”提供，不附带任何明示或默示担保。

Skill 的运行规范以 [`SKILL.md`](SKILL.md) 为准。
