# 全线统一背景音乐（BGM）配置

> 用户固定指定：所有课件视频只使用班得瑞（Bandari）《雪之梦》（Snowdreams），舒缓纯音乐。没有备选曲目，也不得由 Agent 自选或静默换曲。此决定覆盖旧的 Local Forecast 默认配置和许嵩曲库备选设置。

## 唯一指定曲目

- **曲名**：雪之梦（Snowdreams）
- **艺人**：班得瑞（Bandari）
- **风格**：舒缓、空灵的纯音乐
- **完整音源**：用户提供的 `E:/downloadAll/chrome/5629.mp3`，原长 293.382 秒。
- **统一起点**：从原曲约 00:45 截至曲尾；当前处理后的 BGM 段长 248.382 秒，路径为 `assets/bgm/snowdreams/Snowdreams_from_45s.mp3`。
- 后续所有课件直接使用该截取段循环，不再更换起点或询问曲目。Apple Music 的 30 秒试听片段只供试听，不能替代这份完整截取段。
- 完整音源与截取段都保存在本机非公开位置，已加入本机 Git exclude；不把音频文件、账户凭据或购买记录提交 Git、SQLite 或项目快照。

## 混音标准

- 音量：纯音乐默认 `volume=0.18`，不得盖过 PPT 内部音频。
- 无缝循环：`-stream_loop -1` 并以视频时长截断。
- 视频流零重编码，只重混音轨。
- 按下列标准命令使用 45 秒起截取段生成 BGM 派生版：

```bash
ffmpeg -i <视频.mp4> -stream_loop -1 -i assets/bgm/snowdreams/Snowdreams_from_45s.mp3 \
  -filter_complex "[1:a]volume=0.18,atrim=0:VIDEO_SECONDS,asetpts=PTS-STARTPTS[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest <输出_BGM.mp4>
```

## 当前状态

- 完整音源已由用户提供；45 秒起截取段已生成并可直接用于后续课件视频。
- Apple Music 官方试听片段另存于当前项目 `outputs/social/zsxq/preview/Bandari_Snowdreams_AppleMusic_preview.m4a`，仅供试听。
- 《春》及其他已生成的视频不会因偏好更新而自动改写；后续重制或重新混音时只允许使用本段《雪之梦》。
