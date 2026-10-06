---
description: 从教参、已有教学设计或公众号文章运行完整教育课件流水线。
argument-hint: "[教参路径、教学设计路径或微信公众号链接]"
skills: read-wechat-articles,codex-ppt,image-to-editable-ppt,ppt-pipeline-catalog,ppt-animation-video,ppt-social-publishing
---

请在当前工作区运行完整教育课件流程，输入为：$ARGUMENTS

严格按当前工作区 `AGENTS.md` 的固定链路执行：先由 agent-a 读取并处理教学设计，生成正式 Word 文档和交接包；检查并执行必需的 AI 赋能任务；有 HTML 任务时调用 agent-html；再由 agent-b 生成大纲、确认主风格、调用 codex-ppt 生成视觉稿、调用 image-to-editable-ppt 完全拆解为可编辑 PPTX；用户要求时继续做逻辑动画、完整视频和微信公众号发布。

不要固定页数，不要出现艺术字或流程说明性占位文字。每一阶段都必须读取对应的 Agent/Skill 原文、保存真实产物和 QA 证据，并在完成前运行 AI 门禁校验。API 密钥只从本地 `.env` 读取，不能输出或提交。
