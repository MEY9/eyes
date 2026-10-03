# PPT Pipeline Catalog Schema

SQLite is the coordination index for the education PPT pipeline. It is not the source of truth for slide content or style-pack contents.

## Tables

- `decks`: one record per课件 project; stable `deck_id` points to the project directory.
- `styles`: versioned reusable PPT visual systems. The primary key is `style_key`, formatted as `style_id@version`.
- `deck_styles`: links a deck to its candidate, locked, or used style.
- `style_sources`: GitHub and other references used to derive a style.
- `style_samples`: approved sample pages and their hashes.
- `pipeline_runs`: stage ownership and status for Agent A, Agent B, and downstream skills.
- `ai_task_state.json`: project-level AI task status and artifact evidence consumed by the `ai_enrichment` gate.
- `artifacts`: output paths, hashes, role, and stage provenance.
- `approvals`: sample, final-deck, and style-promotion approvals.
- `publication_packages`: one multi-platform delivery package linked to a deck and fixed WeChat layout.
- `publication_variants`: per-platform ratio, video/HTML/copy paths, tags, status, and provenance.

## Invariants

1. Every downstream run has the same `deck_id` as Agent B.
2. Every visual and editable output is registered as an artifact before the stage is marked `passed`.
3. `locked` means approved for this deck only; `verified` means the complete PPT has been approved and the style is reusable.
4. A style version is never silently overwritten.
5. API keys, OCR tokens, prompt secrets, and user private data never enter SQLite.
6. The database can be rebuilt from project files and exported catalog snapshots.
7. A `publication_package` does not replace the `video` run and does not promote a style; it only records platform delivery outputs.
8. `ai_enrichment` must pass before `visual_deck`, `editable_rebuild`, `animation_qa`, `video`, or `publication_package` can be marked `passed`.
9. Every required AI task has a real artifact/evidence path; an outline label, prompt-only file, or static fallback alone is not completion evidence.
