from __future__ import annotations

"""
project_guard.py — token-friendly, privacy-first guard rail for the data-explorer repo.

Output:
  PASS
  WARN <codes...>
  FAIL <codes...>

Exit codes:
  0 PASS
  1 WARN
  2 FAIL
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MISTRAL_CLIENT = ROOT / "llm" / "mistral_client.py"

ALLOWED_LLM_FILES = {str(MISTRAL_CLIENT.resolve())}

LLM_CALL_PATTERNS = [
    r"\bmistralai\b",
    r"\bMistral\s*\(",
    r"\bchat\.complete\b",
    r"https?://api\.mistral\.ai",
]

LEAK_PATTERNS = [
    r"logger\.(info|warning|error)\(.*\bprompt\b",
    r"logging\.(info|warning|error)\(.*\bprompt\b",
    r"logger\.(info|warning|error)\(.*\b(df|dataframe|sample_rows|row[s]?)\b",
    r"logging\.(info|warning|error)\(.*\b(df|dataframe|sample_rows|row[s]?)\b",
]

INVARIANTS = {
    "system_role": [r"role['\"]\s*:\s*['\"]system['\"]"],
    "size_guard": [r"SIZE_LIMIT_BYTES", r"200\s*\*\s*1024"],
    "trunc_warn": [r"AI payload truncated"],
}

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def iter_py_files(root: Path) -> list[Path]:
    skip = {".venv", "venv", "__pycache__", ".git", ".codex", "node_modules"}
    files: list[Path] = []
    for p in root.rglob("*.py"):
        if any(part in skip for part in p.parts):
            continue
        files.append(p)
    return files

def check_invariants() -> list[str]:
    if not MISTRAL_CLIENT.exists():
        return ["missing:mistral_client.py"]
    text = read_text(MISTRAL_CLIENT)

    def has_any(patterns: list[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    fails: list[str] = []
    if not has_any(INVARIANTS["system_role"]):
        fails.append("invariant_missing:system_role")
    if not has_any(INVARIANTS["size_guard"]):
        fails.append("invariant_missing:size_guard_200kb")
    if not has_any(INVARIANTS["trunc_warn"]):
        fails.append("invariant_missing:truncation_warning")
    return fails

def find_llm_calls_outside_client() -> list[str]:
    warns: list[str] = []
    for p in iter_py_files(ROOT):
        text = read_text(p)
        if any(re.search(pat, text, re.IGNORECASE) for pat in LLM_CALL_PATTERNS):
            if str(p.resolve()) not in ALLOWED_LLM_FILES:
                warns.append(f"llm_call_outside_client:{p.relative_to(ROOT)}")
    return warns

def check_leak_risks() -> list[str]:
    warns: list[str] = []
    for p in iter_py_files(ROOT):
        text = read_text(p)
        if any(re.search(pat, text, re.IGNORECASE) for pat in LEAK_PATTERNS):
            warns.append(f"leak_risk_logging:{p.relative_to(ROOT)}")
    return warns

def main() -> int:
    fails = check_invariants()
    if fails:
        print("FAIL " + " ".join(fails[:30]))
        return 2

    warns: list[str] = []
    warns.extend(find_llm_calls_outside_client())
    warns.extend(check_leak_risks())

    if warns:
        print("WARN " + " ".join(warns[:30]))
        return 1

    print("PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
