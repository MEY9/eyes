# 全线统一背景音乐（BGM）配置

> 用户固定指定：所有课件视频只使用班得瑞（Bandari）《雪之梦》（Snowdreams），舒缓纯音乐。没有备选曲目，也不得由 Agent 自选或静默换曲。此决定覆盖旧的 Local Forecast 默认配置和许嵩曲库备选设置。

## 唯一指定曲目

- **曲名**：雪之梦（Snowdreams）
- **艺人**：班得瑞（Bandari）
- **风格**：舒缓、空灵的纯音乐
- **音源来源**：用户本地已有的完整音源，或用户可通过官方渠道获取的完整音源。Apple Music 的 30 秒试听片段不是完整 BGM 音源。
- 如果工作区里还没有完整音源，保持静音母版，并把该课件的 BGM 派生状态记为 `awaiting_snowdreams_audio`；不生成带其他曲目的版本，不因缺音源重复询问曲目选择。
- 用户提供的音源保存在本机非公开路径；不把音频文件、账户凭据或购买记录提交 Git、SQLite 或项目快照。

## 混音标准

- 音量：纯音乐默认 `volume=0.18`，不得盖过 PPT 内部音频。
- 无缝循环：`-stream_loop -1` 并以视频时长截断。
- 视频流零重编码，只重混音轨。
- 完整音源就绪后，将输入路径替换为该音源，按下列标准命令生成 BGM 派生版：

```bash
ffmpeg -i <视频.mp4> -stream_loop -1 -i <已授权班得瑞音源.mp3> \
  -filter_complex "[1:a]volume=0.18,atrim=0:VIDEO_SECONDS,asetpts=PTS-STARTPTS[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest <输出_BGM.mp4>
```

## 当前状态

- Apple Music 官方试听片段已保存到当前项目 `outputs/social/zsxq/preview/Bandari_Snowdreams_AppleMusic_preview.m4a`，时长 30 秒，仅供试听，不能代替完整音源。
- 《春》及其他已生成的视频不会因偏好更新而自动改写；后续重制或重新混音时只允许使用《雪之梦》。
