# Style Library

Read this when the user asks to save a finished PPT deck style, or when the Agent B workflow reaches the post-approval style-promotion gate for a completed PPT/PPTX.

The goal is to save a reusable visual system, not the current deck's private content.

User custom styles are saved to `${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/`, outside the skill install directory, so they survive skill updates and reinstalls. Never write user custom styles into the skill's own `references/` directory; that directory is reserved for built-in styles shipped with the skill.

## When To Use

Use this workflow when the user says things like:

- Save this style.
- Add this PPT style to the style library.
- Let future decks use this style.
- Turn this image/PDF/PPT/PPTX style into a built-in reference.
- Save the style from the finished deck.

For a normal Agent B run, a sample set only creates a temporary project Style Lock. Do not write a reusable system style after sample approval alone. Promote the style only after the complete deck has passed its final QA and the user confirms the complete PPT is acceptable. If the user explicitly asks to save a style earlier, record that exception in the project approval file.

The PPT workflow has two outputs:

- Project snapshot: a `style/` directory inside the current deck project, preserving the exact Style Lock, source records, sample set, page-role rules, prompt rules, version, and approval evidence used for this deck.
- System reusable record: a content-neutral `{style_name}.md` under `${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/`, with optional visual-reference copies under `${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/style-samples/{style_id}/`.

The system record is a reusable PPT visual system, not a copy of the PPTX, a page screenshot, or a collection of task-specific prompts.

## Inspect The Visual Source

Use the actual visible pages as the source of truth.

- For a finished codex-ppt deck, inspect the final `origin_image/slide_XX.png` files or exported slide page images.
- For a sample slide, inspect the approved sample image.
- For user-provided image references, inspect the image itself.
- For PDF/PPT/PPTX references, first render or export representative pages/slides into real page images, then inspect those images. Do not infer the style from file structure, text, XML, metadata, or object hierarchy alone.

Inspect enough pages to capture the style system. Prefer at least one cover or opener, one ordinary content slide, one diagram/process/data slide when available, and one closing or summary slide. If the deck has obvious section-specific variants, record those variants inside the style file.

## Extract The Style System

Extract reusable visual rules:

- `style_name`: short reusable name.
- `best_for`: suitable scenarios and audiences.
- `visual_direction`: one concise description of the style identity.
- `canvas`: aspect ratio, background, composition, density, whitespace.
- `color_palette`: primary, secondary, accent, neutral colors, plus usage rules.
- `typography`: title, body, labels, hierarchy, alignment, text quality rules.
- `layout_patterns`: recurring page types and composition patterns.
- `layout_usage_rule`: how to vary layouts while keeping the same identity.
- `layout_blueprints`: 2-4 reusable composition blueprints, described semantically rather than copied from one slide.
- `visual_elements`: allowed and avoided icons, diagrams, cards, textures, decorations, photos, charts.
- `image_treatment`: how photos, screenshots, charts, or illustrations are handled.
- `rendering_constraints`: rules the image model should follow.
- `style_id`: stable lowercase identifier for reuse.
- `version`: semantic version of the visual system.
- `source_records`: GitHub and other style references, with the exact parts adapted and the reason for adaptation.
- `page_role_rules`: how cover, opener, teaching, activity, practice, feedback, summary, and homework pages vary while sharing the same identity.
- `prompt_rules`: reusable positive and negative prompt rules, including ordinary Chinese typography and no artistic lettering.
- `approval`: final user confirmation evidence and the completed PPT QA state that made the style reusable.

Do not save private or one-off content as style:

- Do not save the user's original article text, business data, personal information, customer names, private project names, paper results, exact quotes, or slide copy.
- Do not make source images or screenshots required dependencies of the style file. Optional approved sample copies may be stored for human comparison and, only when the selected image backend supports it, as style-only reference images; text rules must remain sufficient for reuse.
- Do not preserve identifiable logos or brand names unless the user explicitly asks for a reusable brand style.
- Do not make the style depend on external files; the style file must be self-contained.

## Name The Style

Name the system style file:

```text
${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/{style_name}.md
```

Create the directory first if it does not exist.

Naming rules:

- Prefer a short Chinese style name, usually 2-8 Chinese characters or a concise Chinese phrase.
- Name the reusable visual style, not the project, client, paper, or event.
- Avoid personal names, company names, customer names, paper titles, or temporary task names.
- Avoid vague names like `我的风格1`, `好看风`, or `新风格`.
- Good examples: `深色数据科技风`, `极简发布会风`, `柔和学术插画风`, `高密度咨询风`.

If the target filename already exists, do not overwrite it silently. If it is the same visual system, record reuse of the existing version. If it has changed, create a new semantic version and record the parent version in the project snapshot. If the filename matches a built-in style in the skill's `references/`, the custom file takes priority; preserve the built-in file and use a distinct user-style ID when necessary.

## Write The Style File

Match the structure of the built-in files in the skill's `references/`:

    # {style_name}

    **适用场景:**
    - ...
    - ...

    **GPT-Image-2 风格 Brief:**
    ```json
    {
      "type": "16:9 full-slide PowerPoint image",
      "style_name": "{style_name}",
      "best_for": "...",
      "visual_direction": "...",
      "canvas": {
        "aspect_ratio": "16:9",
        "background": "...",
        "composition": "...",
        "density": "..."
      },
      "color_palette": {
        "primary": "...",
        "secondary": "...",
        "accent": "...",
        "neutral": "...",
        "rule": "..."
      },
      "typography": {
        "title": "...",
        "body": "...",
        "labels": "...",
        "text_quality": "..."
      },
      "layout_patterns": [
        "...",
        "..."
      ],
      "layout_usage_rule": "...",
      "layout_blueprints": [
        {
          "name": "...",
          "sections": [
            {"position": "...", "count": 1, "labels": ["..."]}
          ]
        }
      ],
      "visual_elements": {
        "allowed": "...",
        "avoid": "..."
      },
      "image_treatment": {
        "photos": "...",
        "screenshots": "...",
        "charts": "...",
        "illustrations": "..."
      },
      "rendering_constraints": [
        "...",
        "..."
      ]
    }
    ```

The JSON should be directly reusable as a slide generation style brief. Keep it descriptive enough for future agents, but avoid embedding task-specific content.

## Project Snapshot

Before writing the system record, save the project-local snapshot:

```text
{deck_project}/style/
├── style-lock.yaml
├── style-guide.md
├── prompt-rules.md
├── page-role-rules.md
├── references/
│   ├── sample-cover.png
│   ├── sample-teaching.png
│   └── sample-activity.png
├── source-records.yaml
├── contact-sheet.png
└── approval.md
```

The snapshot may refer to the final deck for audit purposes, but the system style record must remove deck-specific teaching content, private information, and one-off assets. Write the final linkage to `deck_spec.json` as:

```json
{
  "style_library_record": {
    "style_id": "chinese-textbook-picturebook",
    "version": "1.0.0",
    "status": "verified",
    "project_snapshot": "style/",
    "system_path": "${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/chinese-textbook-picturebook.md",
    "approved_after": "complete-deck-user-confirmation"
  }
}
```

## Discovery

No registration step is needed. Future style confirmation steps scan `${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/` and merge its files with the built-in style list, so the saved file is discoverable automatically. Do not edit `docs/outline-style-and-sample.md` or any other file inside the skill for a user custom style.

## Final Response

Report:

- The new style name.
- The style ID and version, plus whether it was reused or created as a new version.
- The saved file path under `${CODEX_PPT_HOME:-~/.codex-ppt-skill}/references/`.
- The project snapshot path and the final-deck approval evidence.
- That the style is stored outside the skill install, so it survives skill updates and reinstalls.
- A one-sentence note on how to request it later, for example: "以后可以说：用「深色数据科技风」生成这份 PPT。"
