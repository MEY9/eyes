# A、HTML、B 课件生产流水线契约

本文件是教学设计、HTML互动课件、正式课堂PPT、可编辑重建、动画和视频之间的共享契约。它不替代各 Agent 或 skill 的详细执行规则，而是规定跨阶段必须保持一致的信息。

## 1. 统一项目文件

每个课件项目建议在项目根目录保存：

```text
source_materials/             原始教参、教学设计、网页归档
working/source_audit.md       来源读取范围、完整性和不确定项
working/lesson_packet.json    A交给HTML和B的机器可读交接包
working/pipeline_state.json   全流程状态与门禁
working/rights_manifest.md    图片、视频、音乐、字体和API来源记录
working/content_traceability.csv
                              教学内容到页面、对象和动画组的追踪
resources/                    可交付资源和静态备用
html_embeds/                  HTML互动课件及其验证产物
outputs/                      正式DOCX、PPTX、MP4和最终报告
```

## 2. lesson_packet.json

`lesson_packet.json` 是 A、HTML 和 B 之间的机器交接源。Markdown、DOCX 和交接说明继续服务人工阅读，但不能与此文件发生冲突。

最低字段：

```json
{
  "schema_version": 1,
  "course": {"title": "", "subject": "", "grade": "", "textbook": "", "unit": "", "lesson": "", "hours": 1},
  "source": {"source_audit": "working/source_audit.md", "teaching_design": "working/teaching_design.docx", "teaching_design_source": "source_materials/"},
  "teaching_contract": {"objectives": [], "key_points": [], "difficult_points": [], "must_keep_steps": [], "assessment": [], "homework": []},
  "ai_tasks": [{"ai_id": "AI-01", "ai_type": "HTML|AI视频|AI素材|AI辅助任务", "required": true, "status": "planned", "execution_owner": "Agent HTML|Agent B", "lesson_step": "", "objective": "", "teacher_action": "", "student_action": "", "duration": "", "verification": "", "fallback": "", "resource_path": "", "rights_status": ""}],
  "constraints": {"formal_document_font": "宋体", "formal_document_size": "五号", "formal_document_color": "黑色", "one_lesson_stays_one_lesson": true},
  "handoff": {"open_questions": [], "change_log": "working/change_log.md", "rights_manifest": "working/rights_manifest.md"}
}
```

规则：

1. `hours` 由来源和用户确认决定，B不得通过增加页面改变课时。
2. `ai_tasks` 至少有一个有效项目，但不要求同时使用 HTML、AI视频和AI素材；只有明确标记为可选的任务才能使用 `required=false`。
3. AI 任务状态按 `planned → running → artifact_ready → qa_passed → integrated → delivered` 推进；失败使用 `failed`，可选且跳过的任务使用 `not_applicable`。
4. HTML项目只有在实际生成单文件HTML、预览图、静态备用、`embed-spec.json`、`runtime-check.json` 和 `task-result.json` 并通过离线验证后，才能把状态推进到 `qa_passed`。
5. `ai_enrichment` 未通过前，不能进入视觉稿、可编辑重建、动画、视频或发布阶段。
4. 无法确认的来源、事实或课堂安排必须写入 `open_questions`，不能用猜测填充。

## 3. pipeline_state.json

所有阶段通过状态文件记录，不以文件是否存在推断完成。

```json
{
  "schema_version": 1,
  "project": "",
  "stages": {
    "source_reading": {"status": "pending", "evidence": []},
    "agent_a": {"status": "pending", "evidence": []},
    "ai_enrichment": {"status": "pending", "evidence": [], "tasks": []},
    "agent_b_outline": {"status": "pending", "evidence": []},
    "visual_draft": {"status": "pending", "evidence": []},
    "editable_rebuild": {"status": "pending", "evidence": []},
    "ppt_animation": {"status": "not_applicable", "evidence": []},
    "video": {"status": "not_applicable", "evidence": []},
    "final_acceptance": {"status": "pending", "evidence": []}
  },
  "blocking_issues": [],
  "last_updated": ""
}
```

允许的状态为 `pending`、`in_progress`、`passed`、`failed`、`not_applicable`。只有证据路径真实存在并通过对应门禁，阶段才能标记为 `passed`。

## 4. 跨阶段门禁

1. A完成前，必须有来源审计、教学设计、变更记录、AI清单和 `lesson_packet.json`。
2. HTML启用时，必须有单文件HTML、预览图、静态备用、`embed-spec.json` 和离线运行验证记录。
3. B开始生成视觉稿前，必须锁定课题、教材版本、课时、大纲和AI页面位置。
4. 进入可编辑重建前，视觉稿必须完成逐页视觉QA。
5. 进入动画或视频前，最终PPTX必须通过对象级重建和结构验证。
6. 最终交付前，内容追踪、资源备用和视频验证必须闭环。

## 5. 内容追踪

`content_traceability.csv` 至少包含以下列：

```text
content_id,teaching_step,source_reference,slide_no,slide_role,text_object_ids,visual_object_ids,animation_group_ids,status,notes
```

每一条教学重点、课堂问题、学生活动、AI任务和作业都应能追踪到页面。没有对应页面或对象时，状态必须为 `missing`，不能静默忽略。

## 6. 来源记录

`source_audit.md` 记录来源URL或文件、读取日期、读取范围、是否完整、OCR或人工复核情况、事实不确定项和替代材料。

`rights_manifest.md` 只做资源来源追溯，记录图片、视频、音乐、字体、HTML资源和外部API的来源与替换方案；不做版权与授权审查，不因版权问题阻塞流程。密钥只能放在 `.env`，不能写入这些清单。
