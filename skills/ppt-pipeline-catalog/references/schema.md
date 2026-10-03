# PPT Pipeline Catalog Schema

SQLite is the coordination index for the education PPT pipeline. It is not the source of truth for slide content or style-pack contents.

## Tables

- `decks`: one record per课件 project; stable `deck_id` points to the project directory.
- `styles`: versioned reusable PPT visual systems. The primary key is `style_key`, formatted as `style_id@version`.
- `deck_styles`: links a deck to its candidate, locked, or used style.
- `style_sources`: GitHub and other references used to derive a style.
- `style_samples`: approved sample pages and their hashes.
- `pipeline_runs`: stage ownership and status for Agent A, Agent B, and downstream skills.
- `artifacts`: output paths, hashes, role, and stage provenance.
- `approvals`: sample, final-deck, and style-promotion approvals.

## Invariants

1. Every downstream run has the same `deck_id` as Agent B.
2. Every visual and editable output is registered as an artifact before the stage is marked `passed`.
3. `locked` means approved for this deck only; `verified` means the complete PPT has been approved and the style is reusable.
4. A style version is never silently overwritten.
5. API keys, OCR tokens, prompt secrets, and user private data never enter SQLite.
6. The database can be rebuilt from project files and exported catalog snapshots.
