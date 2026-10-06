---
name: ppt-animation-video
description: Create one continuous MP4 from a completed editable PPTX and its semantic animation manifest, including full embedded-video playback and only audio already contained in the PPT. Default to player-free semantic composition; use native PowerPoint or WPS recording only when the user explicitly requires exact engine playback. Use after editable reconstruction and animation QA, not for deck authoring or social-platform framing.
---

# PPT 动画视频

## 定位

本技能把 Agent B 已完成的可编辑 PPTX、逻辑动画清单和内嵌媒体合成为一条连续课件视频。默认不启动 PowerPoint 或 WPS，而是依据对象级动画语义重建播放过程；只有用户明确要求“原生放映”“必须与 PowerPoint/WPS 完全一致”时，才切换到原生录制模式。

两种模式必须如实标注，不得把语义合成视频声称为原生录屏，也不得用静态整页切换冒充对象级动画。

固定原则：

- 从第 1 页按 PPT 实际顺序播放到最后一页，页数、动画组数和媒体时长从当前项目读取，不沿用旧课件或固定 19 页。
- 每个语义动画组必须播放一次；动画顺序、组合关系和课堂逻辑以 `animation_manifest_logic.json` 为准。
- 内嵌视频在指定动画组结束后自动开始，完整播放结束后才继续下一步或切页。
- 只保留 PPT 内部已有声音；不添加外部背景音乐、Azure 旁白、后期音效或麦克风声音。
- 保留 PPT 的原始画幅，默认 16:9；不添加页码、进度条、竖版外框、说明文字、外部封面或平台装饰。
- 不设一分钟上限；总时长由动画、媒体和必要的阅读停留共同决定。

## 模式选择

### 模式 A：语义动画合成（默认）

适用于绝大多数交付：依据可编辑 PPTX 的对象、逻辑动画清单和媒体计划生成完整 MP4，无需打开 PowerPoint/WPS。该模式可稳定复现对象逐步显现、淡入、擦除、缩放和组合动画，并把真实内嵌视频及其原声接入时间线。

### 模式 B：原生放映录制（仅明确要求时）

仅当用户明确要求精确复现 PowerPoint/WPS 特有效果、复杂路径动画、Morph、交互触发器或原生播放引擎行为时使用。优先 PowerPoint，WPS 必须先做兼容性测试。若缺少应用、录屏权限或应用音频捕获能力，应阻断并说明，不得伪造原生录制结果。

## SQLite Catalog 协同

沿用 Agent B 传入的 `deck_id`、`style_id@version`、`catalog_db` 和 `run_id`，只读取已通过的可编辑 PPTX与动画 QA artifact。

- 模式 A 登记动画 manifest、媒体计划、合成配置、实际时间线、输出 MP4、哈希和 QA。
- 模式 B 另行登记原生播放计划、录制配置、实际录制日志、PPT 内音轨证据和 QA。
- 只有视频文件存在且全量 QA 通过后，才把 `video` run 标记为 `passed`。
- 本技能不修改 Style Lock、风格版本或用户审批状态，不触发风格入库。
- 密钥、录屏权限数据和私密素材不得写入 Git、SQLite 或对外交付日志。

## 输入门禁

开始前必须确认：

- 最终可编辑 PPTX 可正常打开，页数、顺序、文字、对象和媒体完整。
- `working/animation_manifest_logic.json` 与 PPTX 对象和页面一致，已通过动画结构 QA。
- 动画清单按教学语义划分组合，不是给每个元素机械套同一种效果。
- 所有媒体文件真实存在，可解码，并已确定所属页、对象 ID、播放触发点和实际时长。
- 需要在其他动画之后播放的视频，媒体计划明确 `slide`、`after_group`、`shape_id` 和文件路径。
- 静态海报只是离线备用，不得替代真实视频。

缺少可编辑 PPTX、动画 manifest 或必需媒体时必须阻断。不得只使用最终整页图制造简单翻页视频后声称完成。

## 模式 A 完整流程

### 1. 建立媒体计划

生成 `working/semantic_video_media_plan.json`。每个媒体至少记录：

- 页码、对象 ID/对象名和媒体文件；
- 在第几个动画组之后开始；
- PPT 页面内的 x、y、width、height 或可验证的对象边界；
- 真实时长、是否保留原声、首尾稳定帧和备用海报；
- 播放结束后继续本页下一组还是进入下一页。

媒体时长必须由文件探测获得，不得凭提示词或文件名猜测。

### 2. 渲染对象级累计状态

- 从 PPTX 中解析每页可编辑对象，按照 manifest 的语义组生成累计可见状态。
- 每个组完成后的画面应保留前序组的可见结果；背景和固定版式始终存在。
- 同组对象保持同步，组内不得被拆成无意义的逐字、逐图标动画。
- 使用 LibreOffice/PowerPoint 渲染中间状态后，检查字体、文字、图片、形状、图表和层级是否与最终 PPT 一致。
- 不得用原始高质量页面图覆盖可编辑对象来掩盖字体或排版问题；缺字体时先安装或替换为批准字体并重新渲染。

### 3. 合成逻辑动画

根据 manifest 为相邻累计状态生成过渡：

- `appear`：直接出现，适合答案揭示或明确步骤；
- `fade`：淡入，适合标题、说明和轻量素材；
- `wipe`：按阅读/流程方向擦除，适合流程线、表格行和步骤卡；
- `zoom`：轻微缩放进入，适合核心结论、关键图片或任务卡。

效果应由内容逻辑决定，不能全套使用同一种动画。默认 30 fps，单组动画和停留时长由 manifest/config 控制；不得为了缩短视频连续快切到无法阅读。

项目内置脚本：

```bash
python3 skills/ppt-animation-video/scripts/render_semantic_video.py \
  --input <最终可编辑PPTX> \
  --manifest working/animation_manifest_logic.json \
  --media-plan working/semantic_video_media_plan.json \
  --state-dir working/semantic-video/states \
  --base-output working/semantic-video/base.mp4 \
  --timeline working/semantic_video_timeline.json \
  --output outputs/<课题>_课件语义动画_16x9.mp4
```

实际参数以脚本 `--help` 为准；帧率、过渡时长、停留时长和媒体尾帧缓冲等参数同时写入 `semantic_video_config.json`，并通过对应命令行参数传给脚本。需要的中间文件统一放入 `working/semantic-video/`，QA 抽帧放入 `qa/semantic-video/`。

### 4. 插入真实媒体与内部声音

- 到达媒体计划指定时间点后，在 PPT 对象边界内播放真实视频，不放大到页面外，也不覆盖其他应保留的版式元素。
- 媒体完整播放，禁止加速、截断或在媒体结束前进入下一步。
- 只混入该媒体自身原声或 PPT 已有音频；其余时间保持静音。
- 若 PPT 全程没有内部声音，可保留兼容性的静音 AAC 音轨，但不得用外部音乐填补。
- 媒体结束后恢复 PPT 时间线，继续本页剩余动画或进入下一页。

### 5. 输出与封装

- 输出 H.264 视频、AAC 音频、30 fps 的连续 MP4。
- 分辨率跟随 PPT 画幅，16:9 默认使用 1920×1080。
- 只裁掉合成器的技术空白，不删除教学停留、动画过程或媒体内容。
- 建议文件名：`outputs/<课题>_课件语义动画_<ratio>.mp4`。

## 模式 B 原生录制流程

用户明确要求原生引擎时：

1. 生成 `working/native_playback_plan.json`，记录实际页数、动画组、媒体、触发事件和等待时间。
2. 使用 PowerPoint 或经验证的 WPS 全屏放映，隐藏编辑界面、指针、通知、Dock 和菜单栏。
3. 录制程序按计划触发点击；同组的 `withEffect`、`afterEffect` / `afterPrevious` 由 PPT 自身执行。
4. 媒体自动开始后等待完整时长和结尾缓冲，不额外点击媒体封面。
5. 只捕获应用/系统输出，关闭麦克风；不添加外部声音。
6. 记录 `native_recording_config.json` 和 `native_recording_log.json` 的实际时间戳。

原生录制仍须遵守本技能的页序、媒体完整播放、内部音轨和无额外画布规则。

## 验收门禁

必须逐项验证：

1. 输出是一个连续 MP4，从第 1 页开始并在最后一页结束。
2. 页数与 PPTX 一致，顺序一致，无跳页、重复页或硬编码页数。
3. manifest 中每个动画组均产生可见变化，顺序和组合关系正确；不存在空组或机械逐元素动画。
4. 动画效果有逻辑差异，不是全程同一种淡入或统一飞入。
5. 每个内嵌视频均在规定组后自动开始，完整播放到结束，媒体结束前没有下一步或切页。
6. 音轨只在 PPT 内部媒体/音频应发声的区间出现；没有麦克风、外部音乐、Azure 旁白或后期音效。
7. 画面只包含 PPT 内容，比例正确，无页码、进度条、平台画布、说明性叠字、录屏控件或鼠标。
8. 文字、字体、图片、形状、层级和颜色与批准 PPT 一致，无乱码、缺字、黑屏、闪帧、裁切或明显抖动。
9. 使用 FFmpeg/ffprobe 验证 MP4 可解码、分辨率、帧率、总时长、视频流和音频流。
10. `semantic_video_timeline.json` 或原生录制日志可核对每页、每组和每个媒体的实际起止时间。
11. QA 报告明确标注“语义动画合成”或“原生放映录制”，不得混淆。

任一动画组缺失、媒体被截断、声音来源不合规、文字失真或模式标注不实，均不得标记为通过。

## 固定项目产物

默认模式 A：

```text
working/animation_manifest_logic.json
working/semantic_video_media_plan.json
working/semantic_video_config.json
working/semantic_video_timeline.json
working/video_qa.md
qa/semantic-video/
outputs/<课题>_课件语义动画_<ratio>.mp4
```

模式 B 另加：

```text
working/native_playback_plan.json
working/native_recording_config.json
working/native_recording_log.json
outputs/<课题>_PPT原生播放录制.mp4
```

## Agent B 调用规则

Agent B 在可编辑 PPTX、逻辑动画和内嵌媒体 QA 通过后调用本技能，至少传入：

- 最终可编辑 PPTX；
- 动画 manifest、媒体清单及真实时长；
- 课题名、实际总页数和输出目录；
- `deck_id`、`style_id@version`、`catalog_db` 和 `animation_qa` / `video` run ID；
- 用户是否明确要求原生 PowerPoint/WPS 录制。

没有明确原生要求时一律使用模式 A。Agent B 接收结果后登记 MP4、所用模式、manifest、媒体计划、实际时间线、哈希和 QA。失败时保留日志并返修，不得用无动画视频、简单翻页或混入外部声音的视频代替。

如需小红书、抖音或视频号竖版包装，将本技能产生的单个 16:9 母版交给 `ppt-social-publishing`；平台包装不得回写或替换本母版。
