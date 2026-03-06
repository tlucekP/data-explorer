$ErrorActionPreference = "Stop"

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.12 -c "import pandas, streamlit" > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $PY = "py -3.12"
    } else {
        $PY = "py -3"
    }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PY = "python"
} else {
    Write-Error "Python interpreter not found."
    exit 1
}

Write-Host "== Preflight: lightweight audit =="
Invoke-Expression "$PY tools/self_check.py"
if ($LASTEXITCODE -ge 2) { exit $LASTEXITCODE }

Write-Host "== Preflight: compile check =="
Invoke-Expression "$PY -m py_compile app.py core/profiler.py llm/context_builder.py llm/mistral_client.py llm/send_guard.py privacy/pii_detector.py privacy/anonymizer.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== Preflight: pytest =="
Invoke-Expression "$PY -m pytest -q"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== Preflight: smoke test =="
Invoke-Expression "$PY tools/smoke_test.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== Preflight: UI layout check =="
Invoke-Expression "$PY tools/ui_layout_check.py"
exit $LASTEXITCODE
