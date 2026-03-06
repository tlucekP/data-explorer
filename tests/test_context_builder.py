from __future__ import annotations

import pandas as pd

from core.profiler import profile_csv
from llm.context_builder import ContextScope, build_context
from privacy.pii_detector import PrivacyMode


def test_strict_limits_sample_and_drops_id_like_columns() -> None:
    df = pd.DataFrame(
        {
            "user_id": [f"user_{i}" for i in range(250)],
            "city": ["Praha"] * 250,
        }
    )
    profile = profile_csv(df)
    context = build_context(
        file_kind="csv",
        profile=profile,
        source_payload=df,
        mode=PrivacyMode.STRICT,
        scope=ContextScope.SCHEMA_STATS_SAMPLE,
    )

    assert context["sample_row_count"] <= 100
    assert context["sample_rows"]
    assert "user_id" not in context["sample_rows"][0]


def test_balanced_allows_up_to_200_rows() -> None:
    df = pd.DataFrame({"id": [f"x{i}" for i in range(250)], "value": list(range(250))})
    profile = profile_csv(df)
    context = build_context(
        file_kind="csv",
        profile=profile,
        source_payload=df,
        mode=PrivacyMode.BALANCED,
        scope=ContextScope.SCHEMA_STATS_SAMPLE,
    )

    assert context["sample_row_count"] <= 200
