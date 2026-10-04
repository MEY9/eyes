---
name: azure-tts
description: 为教育课件和课件动画生成可选的中文讲解配音；使用本机 .env 中的 Azure Speech 配置，按教学设计选择音色。不要处理 AI 视频内部配音。
---

# Azure 课件配音

本技能只处理 PPT/课件本身的旁白或讲解音频。AI 视频内部的角色对白、旁白和声音效果由用户在即梦侧处理，不能用本技能替换或二次配音。

## 触发条件

只有教学设计、`speech.md` 或用户明确要求需要配音时才执行。没有配音教学目的时不生成音频，不为了“有 AI”而添加旁白。

旁白脚本优先来自已确认的 `speech.md` 和教学过程，不朗读页面上的全部文字；每段脚本要对应一个页面或一个教学动作，并保留页面编号、课堂作用和备用方案。

## 后端与配置

使用微软官方 Speech SDK Python 示例的实现方式：

`https://github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/quickstart/python/text-to-speech`

运行时只从进程环境或项目 `.env` 读取配置，不在日志、SQLite、JSON、音频元数据或 Git 中写入密钥。兼容本项目当前历史变量名：

- 规范优先：`AZURE_SPEECH_REGION`、`AZURE_SPEECH_KEY`
- 兼容别名：`AZURE_AREA`、`azure_area`；`AZURE_SPEECH_KEY`、`AZURE_KEY`、`axure_secret`

如果没有可用配置或 SDK 未安装，停止并报告，不把静音文件当作成功。安装依赖前先确认当前 Python 环境；需要安装时使用 `azure-cognitiveservices-speech`。

## 音色选择

根据学段、教学设计和课堂角色选择，不按随机默认音色生成：

- 小学科学/综合实践教师讲解：默认 `zh-CN-XiaoxiaoNeural`，亲切、清晰、节奏平稳；语速通常为 `-5%` 到 `0%`。
- 需要更稳重的知识归纳：可选 `zh-CN-YunyangNeural`，但先试听并检查儿童课堂距离感。
- 课堂角色化的侦探对白：可选 `zh-CN-YunxiNeural` 或 `zh-CN-XiaoxiaoNeural`，仅用于课件旁白，不替代 AI 视频内部声音。

一次课件默认保持一个主讲音色；只有教学设计明确需要“教师讲解/角色提示”区分时才增加第二音色。音色、语速、音高、脚本版本和 QA 结果写入项目 `working/voiceover_manifest.json`。

## 生成与验收

1. 从 `speech.md` 或已确认讲稿中建立逐页/逐动作旁白文本。
2. 选择音色并记录选择理由；先生成一小段试听，检查普通话、断句、数字、单位、磷酸等学科词汇。
3. 生成 WAV 或 MP3，保存到当前项目 `resources/voiceover/`；文件名包含页码或动作编号，不覆盖 AI 视频资源。
4. 检查音频可解码、时长合理、无截断、无空白异常和明显误读；失败时修正文本或 SSML 后重生成。
5. `ppt-animation-video` 若被调用，将旁白作为前景音轨；有旁白时自动压低背景音乐，不能把配音混入 AI 视频源文件。

配音是可选交付物，不改变课件页数和教学设计；静态 PPT 和无旁白视频仍需可独立使用。
