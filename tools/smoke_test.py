from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.profiler import profile_csv
from llm.context_builder import ContextScope, build_context
from llm.mistral_client import _serialize_with_size_guard
from privacy.anonymizer import anonymize_csv
from privacy.pii_detector import PrivacyMode, detect_csv_pii

def make_big_df(rows: int = 2000) -> pd.DataFrame:
    # big text to trigger payload truncation
    long_text = "X" * 500
    return pd.DataFrame({
        "email": [f"user{i}@example.com" for i in range(rows)],
        "iban": ["CZ" + "0"*22 for _ in range(rows)],
        "created_at": ["2025-01-01" for _ in range(rows)],
        "description": [long_text for _ in range(rows)],
        "value": list(range(rows)),
    })

def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)

def main() -> int:
    print("== Smoke test pipeline ==")

    # load
    df = make_big_df(2000)

    # profile
    profile = profile_csv(df)
    assert_true(profile.get("row_count", 0) == len(df), "Profile row_count mismatch.")

    # pii detection
    pii_report = detect_csv_pii(df, mode=PrivacyMode.STRICT)
    assert_true(pii_report.has_pii, "Expected PII to be detected.")

    # anonymize
    anonymized_result = anonymize_csv(df, pii_report)
    anon_df = anonymized_result.anonymized_df
    replaced_counts = anonymized_result.replaced_counts
    assert_true(anon_df is not None, "Expected anonymized dataframe.")
    assert_true(replaced_counts.get("EMAIL", 0) > 0 or replaced_counts.get("BANK", 0) > 0,
                "Expected anonymizer to replace some PII.")

    # context build
    context_payload = build_context(
        file_kind="csv",
        profile=profile_csv(anon_df),
        source_payload=anon_df,
        mode=PrivacyMode.STRICT,
        scope=ContextScope.SCHEMA_STATS_SAMPLE,
    )

    # payload serialize + size guard (must not crash)
    user_payload = {
        "task": "Smoke test",
        "dataset": {
            "schema": context_payload["profile"]["schema"],
            "stats": {k: v for k, v in context_payload["profile"].items() if k != "schema"},
            "sample": context_payload.get("sample_rows", []) * 100,
        },
        "analysis_scope": ["Respond in Czech. Only use provided context."],
    }

    serialized = _serialize_with_size_guard(user_payload)
    size = len(serialized.encode("utf-8"))
    assert_true(size > 0, "Serialized payload should not be empty.")

    decoded = json.loads(serialized)
    ds = decoded.get("dataset", {})
    assert_true(isinstance(ds, dict), "dataset must be a dict in payload.")
    assert_true("sample" not in ds or isinstance(ds.get("sample"), list), "dataset.sample must be list if present.")

    print("PASS: smoke pipeline OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
