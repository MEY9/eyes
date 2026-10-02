# Font Management

This is the authoritative font-handling procedure for `image-to-editable-ppt`. It applies to the parent agent and every page worker before any page is reconstructed or repaired.

## Required sequence

1. Build a font inventory from the source PPTX/PPTX theme, source-page text, OCR output, `text_hints.json`, page inventory, and any explicit project constraints. Include family, weight, style, stretch, language coverage, and the pages that use each font. Treat Chinese glyph coverage as a required capability, not an optional preference.
2. Check the actual renderer environment, not only the editor's font menu. Confirm that the required family and usable weight resolve under the account that will run `editppt`, and note the resolved font file when the platform exposes it. A family name alone is insufficient if the requested weight maps to a different face or a fallback.
3. For every missing font, locate an authoritative and legally usable download source: the font vendor, the font project's official repository, or a reputable distribution page that states the license. Preserve the source URL, license, version, file name, and SHA-256 checksum in the run record. Do not download from an unverified mirror, bypass a license, or use a credential/token from a prompt or document.
4. Install the font to the host's user/system font directory before page reconstruction. Prefer a user-level directory so routine work does not require administrator access. On macOS use `~/Library/Fonts` by default; on Linux use `~/.local/share/fonts` (or the configured user font directory) and refresh with `fc-cache` when available; on Windows use the per-user Fonts directory or the platform's supported user installation mechanism. Do not overwrite an existing font without recording the existing version and the replacement decision.
5. Refresh the font registry or restart the renderer after installation. Re-run the environment check and verify that the requested family and weight resolve to the intended file. If the renderer is a long-lived process, restart that process rather than assuming its font cache changed.
6. Render a small Chinese verification page containing a title, body text, punctuation, numerals, and the smallest text size used by the source. Compare the result visually and by OCR/text inspection for tofu boxes, missing glyphs, unexpected fallback, weight mismatch, clipping, and line-wrap changes. Do not dispatch page reconstruction until this test passes.
7. Write a `font_installation.json` (or an equivalent run-local record) with one entry per requested face. The record must contain: `family`, `style`, `weight`, `pages`, `status`, `source_url`, `license`, `version`, `sha256`, `install_path`, `renderer_check`, `test_page`, `verified_at`, and `notes`. If a substitute is unavoidable, mark the entry `substituted`, name the substitute and reason, and surface it in the final validation report.

## Platform notes

On macOS, install ordinary user fonts under `~/Library/Fonts` and let the operating system register them. Use `/Library/Fonts` only when a system-wide install is explicitly required and authorized. Do not modify protected system font locations or remove fonts as part of this workflow.

On Linux, install to the current user's font directory, refresh the font cache when the command is available, and verify with the same user account that launches the reconstruction runtime.

On Windows, use a per-user font installation path when possible and verify in the same user session that launches the renderer. Avoid silently copying into protected directories.

## Failure policy

Missing-font handling is a hard gate for text fidelity. If a legal authoritative source is available, downloading and installing the font is part of the normal reconstruction workflow and does not require a separate user confirmation. If the source is inaccessible, the license is unclear, administrator privileges are required, or the installed face still fails the Chinese verification page, preserve the evidence, mark the affected pages as blocked or substituted, and report the exact limitation. Never claim a font was installed based only on a filename or a successful HTTP response.
