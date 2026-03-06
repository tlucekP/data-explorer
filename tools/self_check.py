from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_FILES = [
    "app.py",
    "llm/mistral_client.py",
    "llm/context_builder.py",
    "privacy/pii_detector.py",
    "privacy/anonymizer.py",
]

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def _exists_all() -> list[str]:
    missing: list[str] = []
    for rel in CRITICAL_FILES:
        if not (ROOT / rel).exists():
            missing.append(rel)
    return missing

def _flag_mistral_client(text: str) -> list[str]:
    flags: list[str] = []
    if ("SIZE_LIMIT_BYTES" not in text) and ("200 * 1024" not in text) and ("200*1024" not in text):
        flags.append("mistral_client:missing_size_guard")
    if ('"role": "system"' not in text) and ("'role': 'system'" not in text) and ("role\":\"system" not in text):
        flags.append("mistral_client:missing_system_role")
    if "AI payload truncated" not in text:
        flags.append("mistral_client:missing_truncation_warning")
    return flags

def _flag_risky_logging(text: str, rel: str) -> list[str]:
    patterns = [
        r"logger\.(info|warning|error)\(.*\bprompt\b",
        r"logging\.(info|warning|error)\(.*\bprompt\b",
        r"logger\.(info|warning|error)\(.*\b(df|dataframe|sample_rows|row[s]?)\b",
        r"logging\.(info|warning|error)\(.*\b(df|dataframe|sample_rows|row[s]?)\b",
    ]
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return [f"{rel}:risky_logging_pattern"]
    return []

def main() -> int:
    missing = _exists_all()
    if missing:
        print("FAIL missing:" + ",".join(missing))
        return 2

    flags: list[str] = []
    mc = _read(ROOT / "llm/mistral_client.py")
    flags.extend(_flag_mistral_client(mc))

    for rel in CRITICAL_FILES:
        t = _read(ROOT / rel)
        flags.extend(_flag_risky_logging(t, rel))

    if flags:
        print("WARN " + " ".join(flags[:20]))
    return 1

    print("PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
