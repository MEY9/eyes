# Workflow Gates And Progress

Read this before creating downstream artifacts, advancing between phases, or reporting progress.

## Mandatory Phase Gates

This workflow has explicit approval gates. Do not advance to a later phase until the previous phase has been approved by the user, unless the user explicitly asks to skip that confirmation.

Phase order:

1. Source reading and asset extraction
2. Outline confirmation
3. Visual style confirmation
4. Image backend confirmation
5. Representative sample set approval
6. Full slide generation
7. QA, speaker notes finalization, and PPT assembly
8. Complete-deck user confirmation and style-library promotion

Style confirmation includes a single selected style source and a completed `Style Lock`. For multi-page decks, the style gate also includes a thumbnail-board review when feasible. The board checks rhythm and page-role variation; it is not a final slide and does not replace the representative sample set.

Hard rules:

- Before outline approval, do not create final `deck_spec.json`, `speech.md`, prompt job files, slide images, or `.pptx` files.
- If you need an internal planning artifact before approval, name it with `.draft.` such as `deck_spec.draft.json` or `speech.draft.md`, and clearly report that it is not final.
- Downstream artifacts (`deck_spec.json`, `prompts/`, `slide_jobs.json`, `speech.md`, final slide images, and `.pptx`) should be created only after the relevant gates have been approved.
- If the deck uses required source images, stop at outline confirmation and ask the user to verify the slide-to-image mapping before style selection or image generation.

## Visible Progress Plan

For non-trivial decks, keep a user-visible checklist with one active step:

1. Prepare source, outline, style, and backend decisions.
2. Generate and approve a representative sample set.
3. Prepare slide jobs and slide state.
4. Dispatch slide subagents.
5. Record generated slide results.
6. QA, repair, notes, and PPT assembly.
7. After the user confirms the complete PPT, save the project style snapshot and promote the content-neutral style record to the reusable style library.

Completion evidence:

- `Prepare source, outline, style, and backend decisions`: `outline.md` is approved and image backend is confirmed.
- `Generate and approve a representative sample set`: the required cover/opening, normal teaching, and activity/practice/feedback samples are approved as the style references; a documented exception may reduce this to one sample.
- `Prepare slide jobs and slide state`: `prompts/slide_XX.json`, `slide_jobs.json`, and `slide_run_state.json` exist.
- `Dispatch slide subagents`: `slide_job_status.py` shows dispatchable slides and each spawned worker is recorded by `record_slide_dispatch.py`.
- `Record generated slide results`: each worker output is recorded by `record_slide_result.py`, which copies the selected image into `origin_image/slide_XX.png` and records backend provenance.
- `QA, repair, notes, and PPT assembly`: every expected final image exists, QA is complete, `speech.md` is final, and `{deck_name}.pptx` exists.
- `Complete-deck user confirmation and style-library promotion`: the user has confirmed the complete PPT is acceptable; `style/approval.md` records the evidence; `style_library_record` is present in `deck_spec.json`; and the reusable system record exists, unless the user explicitly chose project-only storage.

Do not mark a step complete just because the chat says it is complete; use real files or script-recorded state.
