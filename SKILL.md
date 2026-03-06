---
name: data-explorer
description: Keep data-explorer stable with mandatory Czech/English parity and strict UI/UX layout guardrails (fixed file panel, non-overlapping workspace columns) using self_check, tests, smoke test, and ui_layout_check before finalizing changes. Use for all work in this repository.
---

# Data Explorer Skill

## Purpose
Keep the `data-explorer` application functionally stable while enforcing Czech/English parity for all user-facing text.

## Core Rule
Anything added or changed in Czech must also be added or changed in English in the same implementation.

## Scope
- Streamlit UI labels, buttons, help text, warnings, captions, tab names, and placeholders.
- User documentation shipped in this repository.

## Required Workflow
1. Add or update a translation key instead of hardcoding text directly in UI code.
2. Provide values for both `cs` and `en`.
3. Verify no Czech-only string remains in UI when language is `ENG`.
4. Verify default language stays Czech (`CZE`).
5. Run tests and a syntax check after changes.

## UI/UX Layout Guardrail (mandatory)
1. Treat changes in `ui/styles.py`, `ui/file_panel.py`, `app.py` layout blocks, and sidebar/panel spacing as high-risk layout changes.
2. Change one layout variable at a time and verify effect before changing another layout variable.
3. Preserve the layout contract:
   - `file_panel_shell` stays fixed while scrolling page content.
   - `workspace_layout` top-level columns stay on one row (no wrapping).
   - `file_panel_shell` never overlaps `content_col`.
4. For every layout task, run `python tools/ui_layout_check.py` before and after edits.
5. If `ui_layout_check.py` fails, do not finalize changes; fix CSS/selectors and rerun until `UI_LAYOUT_CHECK: PASS`.

## Safety Notes
- Do not alter privacy guards or LLM send logic when doing translation-only changes.
- Do not log raw PII or demasked values.

## Self-healing protocol (mandatory)
1. Before implementing changes, run `python tools/self_check.py` and read the risk report.
2. If `self_check.py` exits with code `2`, stop and fix failures before further edits.
3. If `self_check.py` exits with code `1`, continue only with explicit review of reported warnings.
4. Keep privacy invariants intact: never send raw PII to AI and never log raw PII.
5. After implementing changes, run:
   - `python -m py_compile app.py core/profiler.py llm/context_builder.py llm/mistral_client.py llm/send_guard.py privacy/pii_detector.py privacy/anonymizer.py tools/ui_layout_check.py`
   - `python -m pytest -q`
   - `python tools/smoke_test.py`
   - `python tools/ui_layout_check.py`
6. Preferred one-command runners:
   - Windows: `powershell -ExecutionPolicy Bypass -File tools/preflight.ps1`
   - POSIX: `bash tools/preflight.sh`

