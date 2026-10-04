---
name: ppt-pipeline-catalog
description: Coordinate education PPT agents and skills with a local SQLite catalog for decks, styles, runs, artifacts, approvals, and provenance; keep Git and project files as the source of truth.
---

# PPT Pipeline Catalog

这是 Agent A、Agent B、codex-ppt、image-to-editable-ppt、HTML、ppt-animation-video 和 ppt-social-publishing 共用的轻量协调层。它只保存索引、状态和来源关系，不替代 Git、课件项目文件、风格包或最终 PPTX。

## 核心原则

- SQLite 是流水线索引和协调状态，不是教学内容、PPTX 或图片的唯一来源。
- Git 和当前课件项目目录中的文件是事实来源；数据库只记录它们的路径、哈希、状态和关系。
- 所有阶段使用同一个 `deck_id`；风格使用 `style_id@version`；运行使用 `run_id`。
- 任何 skill 不得手工改写其他阶段的状态；使用 `scripts/catalog.py` 记录。
- 数据库只保存路径、哈希、元数据和审计信息，不保存 API key、token 或密码。
- 数据库文件是本机运行状态，不提交 Git；schema、脚本和文档必须提交 Git。

## 默认位置

默认数据库：`${CODEX_PPT_HOME:-~/.codex-ppt-skill}/catalog.sqlite3`。

可以使用环境变量 `PPT_PIPELINE_CATALOG_DB` 指定路径，也可以在每条命令中使用 `--db`。数据库目录由脚本自动创建，并启用 SQLite 外键和 WAL。

初始化：

```bash
python3 skills/ppt-pipeline-catalog/scripts/catalog.py init
```

## 统一状态链

```text
source_ingest
→ teaching_design
→ outline
→ style_candidate
→ style_sample_approval
→ ai_enrichment
→ visual_deck
→ editable_rebuild
→ animation_qa
→ video
→ publication_package
→ complete_deck_approval
→ style_promotion
```

Agent A 只负责登记来源和教学设计交接；Agent B 负责登记课件主流程和最终门禁；各 downstream skill 只登记自己拥有的阶段和产物，不改变上游内容。

## 阶段协同

| 组件 | 读取 | 登记 | 不负责 |
|---|---|---|---|
| Agent A | 来源、项目、已有 catalog 记录 | teaching_design、source artifact、handoff | 风格入库、PPT 重建 |
| Agent HTML | Agent A 的 HTML AI 任务 | HTML run、HTML 文件、预览图、静态备用、runtime-check、task-result | 改教学设计、改整份 PPT |
| Agent B | lesson packet、catalog、Style Lock | deck、outline、style candidate、样张、最终 QA、用户确认、style promotion | 伪造 HTML、替代对象重建 |
| codex-ppt | deck、outline、style candidate | visual_deck run、样张、origin_image、视觉版 PPTX | 对象级可编辑重建 |
| image-to-editable-ppt | visual deck、Style Lock、OCR和 catalog | editable_rebuild run、page validation、可编辑 PPTX | 改风格和教学内容 |
| ppt-animation-video | 可编辑 PPTX、动画清单、catalog | animation/video run、MP4、音乐、字体修复和视频 QA | 生成课件、补做对象重建 |
| ppt-social-publishing | 通过 QA 的 3:4/9:16 视频母版、教学元数据、catalog | publication_package run、三个手动平台 variant、公众号 API variant、HTML、文案、标签和发布 QA | 改课件内容、重新制作动画视频 |

## AI 任务门禁

`ai_enrichment` 是从教学设计进入正式 PPT 生成前的强制阶段。Agent B 必须从 `lesson_packet.json` 的 `ai_tasks` 读取任务；旧项目可兼容 `ai_empowerment`，但必须先规范化为 `working/ai_task_state.json`。每项任务使用以下状态：

`planned` → `running` → `artifact_ready` → `qa_passed` → `integrated` → `delivered`

失败使用 `failed`；只有明确标为可选且用户允许跳过的任务才能使用 `not_applicable`。`required` 缺省为 `true`，AI 视频只有在明确“可选/不制作”时才可为 `false`。

执行 `ai_enrichment` 时：

- HTML 任务必须由 Agent HTML 实际执行，并交付单文件 HTML、预览图、静态备用、`embed-spec.json`、`runtime-check.json` 和 `task-result.json`；
- AI 素材任务必须有实际资源文件、提示词、使用页面和静态文字备用，只有提示词不能通过；
- 必需 AI 视频必须有实际视频和 QA，可选视频可以记录 `not_applicable`。如果用户明确要求“AI 视频最后生成”，可在任务中写明 `execution_phase: post_visual_deck` 和延期原因；预视觉门禁可显式允许该视频保持 `planned`，但最终交付前仍必须取得视频并通过 QA；HTML 和 AI 素材不能使用此例外；
- 每个必需任务必须至少关联一个正式课堂页面或明确课堂环节。

使用 `scripts/validate_ai_gate.py` 校验当前项目。校验不通过时，禁止登记 `visual_deck`、`editable_rebuild`、`animation_qa`、`video` 或 `publication_package` 为 `passed`。静态备用是故障回退，不等于必需 AI 任务已完成。

预视觉延期门禁只能显式调用：

```bash
python3 skills/ppt-pipeline-catalog/scripts/validate_ai_gate.py \
  --project "/absolute/path/to/project/PPT课件/课题" \
  --allow-deferred-post-visual \
  --out "working/ai_task_gate.json"
```

该开关只放行写明 `execution_phase: post_visual_deck` 的用户延期 AI 视频；进入最终交付或发布前必须重新执行普通门禁，且视频达到 `qa_passed`、`integrated` 或 `delivered`。

## 标准命令

以下命令都幂等，重复执行会更新对应记录：

```bash
CATALOG="skills/ppt-pipeline-catalog/scripts/catalog.py"

python3 "$CATALOG" init

python3 "$CATALOG" upsert-deck \
  --deck-id "poetry-xing-lu-nan" \
  --title "诗词三首·行路难" \
  --project-path "/absolute/path/to/project"

python3 "$CATALOG" run \
  --run-id "run-visual-001" \
  --deck-id "poetry-xing-lu-nan" \
  --stage visual_deck \
  --status running

python3 "$CATALOG" artifact \
  --deck-id "poetry-xing-lu-nan" \
  --run-id "run-visual-001" \
  --kind origin-image \
  --role slide-01 \
  --path "/absolute/path/to/origin_image/slide_01.png"

python3 "$CATALOG" approval \
  --deck-id "poetry-xing-lu-nan" \
  --stage style_sample_approval \
  --status approved \
  --evidence-path "/absolute/path/to/approval.md"

python3 "$CATALOG" publication \
  --deck-id "poetry-xing-lu-nan" \
  --package-id "publish-poetry-xing-lu-nan-001" \
  --status passed \
  --layout-id "wechat-education-warm-paper@1.0"

python3 "$CATALOG" publication \
  --deck-id "poetry-xing-lu-nan" \
  --package-id "publish-poetry-xing-lu-nan-001" \
  --platform xiaohongshu \
  --status passed \
  --ratio "3:4" \
  --video-path "/absolute/path/to/video_3x4.mp4" \
  --copy-path "/absolute/path/to/copy.txt" \
  --tags-json '["#语文教学", "#课堂课件", "#AI教育", "#小学语文", "#教学设计"]'
```

查询风格：

```bash
python3 "$CATALOG" search-styles --status verified
```

导出不含密钥的审计快照：

```bash
python3 "$CATALOG" export --deck-id "poetry-xing-lu-nan" --out "working/catalog_snapshot.json"
```

校验 AI 交接和实际产物：

```bash
python3 skills/ppt-pipeline-catalog/scripts/validate_ai_gate.py \
  --project "/absolute/path/to/project/PPT课件/课题"
```

## 风格入库门禁

样张批准只能把风格标记为 `locked`，不能写入系统可复用风格。只有完整 PPT、可编辑 PPTX、动画/视频（如有）通过 QA，并且用户确认完整课件无问题后，Agent B 才能：

1. 写入项目 `style/` 快照；
2. 注册 `complete_deck_approval`；
3. 注册 `style_id@version`，状态为 `verified`；
4. 在 `deck_spec.json` 写入 `style_library_record`；
5. 把内容中性的 style record 写入系统风格库。

若用户拒绝复用，只登记 `project-only`，不得写入系统风格库。

## 故障恢复

数据库损坏或不可用时，不删除项目文件，不伪造阶段成功。先运行 `init` 或 `doctor`，保留错误证据；如果本次运行必须继续，所有阶段仍必须把同样的 `deck_id`、`style_id`、`run_id` 写入项目文件，恢复数据库后再导入审计快照。
