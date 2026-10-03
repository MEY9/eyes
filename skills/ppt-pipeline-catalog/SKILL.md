---
name: ppt-pipeline-catalog
description: Coordinate education PPT agents and skills with a local SQLite catalog for decks, styles, runs, artifacts, approvals, and provenance; keep Git and project files as the source of truth.
---

# PPT Pipeline Catalog

这是 Agent A、Agent B、codex-ppt、image-to-editable-ppt、HTML 和 ppt-animation-video 共用的轻量协调层。它只保存索引、状态和来源关系，不替代 Git、课件项目文件、风格包或最终 PPTX。

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
→ visual_deck
→ editable_rebuild
→ animation_qa
→ video
→ complete_deck_approval
→ style_promotion
```

Agent A 只负责登记来源和教学设计交接；Agent B 负责登记课件主流程和最终门禁；各 downstream skill 只登记自己拥有的阶段和产物，不改变上游内容。

## 阶段协同

| 组件 | 读取 | 登记 | 不负责 |
|---|---|---|---|
| Agent A | 来源、项目、已有 catalog 记录 | teaching_design、source artifact、handoff | 风格入库、PPT 重建 |
| Agent HTML | Agent A 的 HTML AI 任务 | HTML run、HTML 文件、预览图、静态备用、runtime-check | 改教学设计、改整份 PPT |
| Agent B | lesson packet、catalog、Style Lock | deck、outline、style candidate、样张、最终 QA、用户确认、style promotion | 伪造 HTML、替代对象重建 |
| codex-ppt | deck、outline、style candidate | visual_deck run、样张、origin_image、视觉版 PPTX | 对象级可编辑重建 |
| image-to-editable-ppt | visual deck、Style Lock、OCR和 catalog | editable_rebuild run、page validation、可编辑 PPTX | 改风格和教学内容 |
| ppt-animation-video | 可编辑 PPTX、动画清单、catalog | animation/video run、MP4、音乐、字体修复和视频 QA | 生成课件、补做对象重建 |

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
```

查询风格：

```bash
python3 "$CATALOG" search-styles --status verified
```

导出不含密钥的审计快照：

```bash
python3 "$CATALOG" export --deck-id "poetry-xing-lu-nan" --out "working/catalog_snapshot.json"
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
