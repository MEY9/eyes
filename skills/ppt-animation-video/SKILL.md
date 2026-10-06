---
name: ppt-animation-video
description: Record a completed animated PPTX as one continuous MP4 by running it in native PowerPoint or WPS slideshow mode. Capture every native animation and embedded video in real time, wait for media playback to finish before advancing, and record only audio already contained in the PPT. Use after editable-PPT reconstruction and animation QA; do not use for static-state simulation, external music or voiceover, platform framing, or deck authoring.
---

# PPT 原生播放录制

## 定位

本技能是 Agent B 的原生幻灯片录制阶段。输入是已完成对象级重建、PPTX 原生动画、内嵌媒体和播放 QA 的可编辑 PPTX；输出是一个连续的 MP4 录制母版。

录制的是 PowerPoint 或 WPS 在幻灯片放映模式下的真实播放结果，不是重渲染静态状态、截图拼接、逐页图片切换或视频后期仿造动画。

固定原则：

- 从第 1 页开始，按 PPT 原有顺序播放到最后一页，录制为一个完整视频。
- 所有 PPT 内动画都必须实际播放，不跳组、不跳页、不用最终状态代替过程。
- 内嵌视频必须在 PPT 内真实播放；视频未结束时不得点击下一步或进入下一页。
- 只录制 PPT 内部已有声音，不添加外部背景音乐、Azure 旁白、后期音效、麦克风声音或其他音轨。
- 画面保留 PPT 放映的原始比例和内容，不额外添加竖版画布、页码、进度条、说明性文字、外部封面或平台装饰。
- 取消一分钟限制；总时长由 PPT 动画、嵌入媒体和必要的步骤间隔决定。

## SQLite Catalog 协同

沿用 Agent B 传入的 `deck_id`、`style_id@version`、`catalog_db` 和 `run_id`。只读取已通过的可编辑 PPTX 和动画 QA artifact，不根据文件名新建课件身份。

- 登记原生播放计划、录制日志、输出 MP4、PPT 内音轨证据和 QA 结果。
- 只有原生播放录制和全量 QA 通过后，才将 `video` run 标记为 `passed`。
- 本技能不修改 Style Lock、风格版本或用户审批状态，不触发风格入库。
- 密钥、录屏权限数据和私密素材不得写入 Git、SQLite 或对外交付日志。

## 输入门禁

录制前必须确认：

- 最终可编辑 PPTX 可正常打开，页数、顺序、文字、对象和媒体完整。
- 动画清单与 PPTX 实际时间线一致，每页的点击组、`withEffect`、`afterEffect` / `afterPrevious` 和页面切换已通过结构 QA。
- 内嵌视频是真实媒体对象，编码可由目标播放引擎解码；静态海报只是备用，不冒充视频。
- 需要在前置动画完成后自动播放的视频，已在 PPTX 中建立原生媒体节点和播放命令，不依赖录制程序去点击视频封面。
- 已获得 PowerPoint 或 WPS 放映所需的屏幕录制、辅助功能和系统/应用音频捕获权限。
- 已识别 PPT 中所有视频和音频对象的时长、播放次数和触发方式。

如果没有可用的 PowerPoint/WPS 原生放映引擎，或录屏器不能捕获 PPT 内部声音，必须阻断并说明原因。不得降级为静态页拼接、状态图仿动画或静音视频后声称完成原生播放录制。

## 完整流程

### 1. 选择原生播放与录制环境

- 优先使用 Microsoft PowerPoint；未安装 PowerPoint 时可使用 WPS，但必须先在含动画和视频的页面上验证兼容性。
- 以幻灯片放映模式播放，隐藏编辑器界面、播放控件、鼠标指针、系统通知、Dock 和菜单栏。
- 录制区域只包含幻灯片播放画面，比例跟随 PPT；默认不重构为 3:4 或 9:16。
- 使用能同时捕获屏幕和应用/系统输出音频的工具，例如 macOS ScreenCaptureKit 或已正确配置的 OBS。麦克风输入必须关闭。
- 录制为单次连续会话；不逐页录制后再拼接，除非发生可证明的播放失败并必须重录整段。

### 2. 生成播放计划

从 PPTX 和动画 manifest 生成 `working/native_playback_plan.json`，至少记录：

- 页码和实际总页数；
- 每页的动画组、触发方式和预计完成时间；
- 页面切换是手动还是自动；
- 每个嵌入视频/音频的对象 ID、对象名、触发点、媒体时长、循环规则和结束后的下一步；
- 每次需要由录制程序发送的点击/键盘事件，以及事件前后的最小安全间隔。

不允许将页数、点击次数或视频时长写死为上一套课件的值。

### 3. 执行完整放映

- 开始录制后从第 1 页进入放映，按播放计划依次触发所有点击动画。
- 同一组内的 `withEffect` 和 `afterEffect` / `afterPrevious` 由 PPT 自身时间线执行；录制程序不额外点击或重放。
- 每次触发后必须等待该组动画完成再触发下一步，不用连点追赶时长。
- 如果最后一组动画之后会自动播放视频，只触发最后一组，随后等待 PPT 自动开始视频；不再点击媒体对象。
- 视频开始后，等待完整媒体时长和少量结尾缓冲后再进入下一步。若 PPT 中设定为循环播放，默认完整录制一个循环后进入下一步；用户或 manifest 有明确次数时按指定执行。
- 页内所有动画和媒体完成后才允许切换页面。自动切页由 PPT 执行；手动切页只在播放计划指定的时点发送一次。
- 最后一页的所有动画和媒体结束后，保留短暂稳定画面，然后结束录制。

### 4. 只录制 PPT 内部声音

- 录屏输入只选择 PowerPoint/WPS 应用音频或系统输出；麦克风、摄像头麦克风和环境收音全部关闭。
- 不调用 `azure-tts`，不下载或添加背景音乐，不在后期添加点击声、转场声或解说。
- PPT 内嵌视频的原声、PPT 内已嵌入的音效和 PPT 自身音频对象属于允许录制的声音。
- 可以为平台兼容进行音频编码转换、空白首尾裁剪和防削波保护，但不得增加新的音频内容、改变声画同步或用外部音乐填补静音。

### 5. 裁剪和封装

- 只裁掉开始放映前和结束放映后的空白时间，不剪掉动画过程、阅读停留或媒体内容。
- 不分段重排、不加速嵌入视频、不替换音轨、不变更页面顺序。
- 保留 PPT 实际放映的宽高比。编码优先使用 H.264 视频和 AAC 音频；如 PPT 全程没有任何内部声音，可保留静音音轨以提高兼容性，但不得添加其他声音。
- 建议输出：`outputs/<课题>_PPT原生播放录制.mp4`。

## 验收门禁

必须逐项验证：

1. 输出是一个连续 MP4，从第 1 页开始并在最后一页结束。
2. 页数与 PPTX 一致，顺序一致，没有跳页或重复页。
3. 动画清单中的每个动画组都在录制中出现，顺序、效果和触发关系与 PPT 实际放映一致。
4. 每个内嵌视频都真实开始、连续播放到结束，视频结束前没有下一步或切页事件。
5. 需要在其他动画之后自动播放的视频，符合“最后一组教学动画完成 → 无额外点击 → 视频自动播放 → 播放结束 → 下一步”。
6. 画面中只有 PPT 放映内容，没有编辑器、鼠标、录屏控件、系统通知、额外页码、进度条或说明性叠字。
7. 音轨只含 PPT 内部声音；麦克风未开启，没有外部音乐、旁白或后期音效。
8. 声画同步，嵌入视频无黑屏、卡顿、截断或静音异常。
9. 无一分钟或其他硬编码时长限制，录制时长覆盖完整 PPT 播放流程。
10. 使用 FFmpeg/ffprobe 或等效工具验证 MP4 可解码、分辨率、帧率、总时长、视频流和音频流；通过时间戳日志核对每页、每组动画和每个媒体的起止点。

任一页动画未完整播放、媒体被跳过/截断、录制时误触下一步、没有捕获 PPT 内部声音或混入麦克风/外部音轨时，整个录制不得标记为通过。

## 固定项目产物

```text
working/animation_manifest_logic.json
working/native_playback_plan.json
working/native_recording_log.json
working/native_recording_config.json
working/video_qa.md
outputs/<课题>_PPT原生播放录制.mp4
```

`native_recording_config.json` 至少记录播放应用及版本、录屏器、录制区域、帧率、系统/应用音频来源、麦克风关闭状态和权限检查结果。`native_recording_log.json` 记录实际播放时间戳，不只保存计划值。

## Agent B 调用规则

Agent B 在 PPTX 原生动画、内嵌媒体和播放结构 QA 通过后调用本技能。至少传入：

- 最终可编辑 PPTX 路径；
- 动画清单路径；
- 嵌入媒体清单及实际时长；
- 课题名、实际总页数和输出目录；
- `deck_id`、`style_id@version`、`catalog_db` 和 `animation_qa` / `video` run ID。

Agent B 接收输出后，必须登记 MP4 路径、PPT 播放引擎、播放计划、实际录制日志、PPT 内声音捕获证据和 QA 结果。失败时保留日志并返修；不得用静态拼接视频、无动画视频或混入外部声音的视频代替。

如果后续需要小红书、抖音或视频号的竖版包装，将本技能产生的单个原生播放母版交给 `ppt-social-publishing` 另行处理。平台包装不得回写或替换本原生录制母版。
