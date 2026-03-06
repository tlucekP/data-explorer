#!/usr/bin/env bash
set -euo pipefail

if command -v python3.12 >/dev/null 2>&1; then
  PY_BIN="python3.12"
elif command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
else
  PY_BIN="python"
fi

echo "== Preflight: lightweight audit =="
"$PY_BIN" tools/self_check.py || rc=$?
rc=${rc:-0}
if [ "$rc" -ge 2 ]; then
  exit "$rc"
fi

echo "== Preflight: compile check =="
"$PY_BIN" -m py_compile \
  app.py \
  core/profiler.py \
  llm/context_builder.py \
  llm/mistral_client.py \
  llm/send_guard.py \
  privacy/pii_detector.py \
  privacy/anonymizer.py \
  tools/ui_layout_check.py

echo "== Preflight: pytest =="
"$PY_BIN" -m pytest -q

echo "== Preflight: smoke test =="
"$PY_BIN" tools/smoke_test.py

echo "== Preflight: UI layout check =="
"$PY_BIN" tools/ui_layout_check.py
