"""Build minimal AI context payload by selected scope and privacy mode."""

from __future__ import annotations

from enum import Enum
from typing import Any

import pandas as pd

from privacy.pii_detector import PrivacyMode, parse_mode


class ContextScope(str, Enum):
    SCHEMA = "schema"
    SCHEMA_STATS = "schema+stats"
    SCHEMA_STATS_SAMPLE = "schema+stats+sample"


ID_LIKE_NAMES = {"id", "user_id", "customer_id", "uuid", "guid", "account_id", "person_id"}


def _sample_limit(mode: PrivacyMode) -> int:
    if mode == PrivacyMode.BALANCED:
        return 200
    if mode == PrivacyMode.RELAXED:
        return 300
    return 100


def _drop_identifier_columns(df: pd.DataFrame) -> pd.DataFrame:
    to_drop: list[str] = []
    for col in df.columns:
        col_l = str(col).lower()
        if col_l in ID_LIKE_NAMES or col_l.endswith("_id"):
            non_null = df[col].dropna()
            if non_null.empty:
                continue
            unique_ratio = float(non_null.nunique() / len(non_null))
            if unique_ratio >= 0.95 and len(non_null) >= 50:
                to_drop.append(col)
    if not to_drop:
        return df
    return df.drop(columns=to_drop, errors="ignore")


def build_context(
    file_kind: str,
    profile: dict[str, Any],
    source_payload: Any,
    mode: str | PrivacyMode,
    scope: str | ContextScope,
) -> dict[str, Any]:
    """Build minimal outbound context for LLM call."""
    parsed_mode = parse_mode(mode)
    parsed_scope = scope if isinstance(scope, ContextScope) else ContextScope(scope)
    context: dict[str, Any] = {
        "file_kind": file_kind,
        "privacy_mode": parsed_mode.value,
        "scope": parsed_scope.value,
        "profile": {},
    }

    if file_kind == "csv":
        context["profile"]["schema"] = profile.get("schema", [])
        if parsed_scope in (ContextScope.SCHEMA_STATS, ContextScope.SCHEMA_STATS_SAMPLE):
            context["profile"]["row_count"] = profile.get("row_count", 0)
            context["profile"]["column_count"] = profile.get("column_count", 0)
            context["profile"]["missing_by_column"] = profile.get("missing_by_column", {})
            context["profile"]["numeric_stats"] = profile.get("numeric_stats", {})
            context["profile"]["duplicate_rows"] = profile.get("duplicate_rows", 0)

        if parsed_scope == ContextScope.SCHEMA_STATS_SAMPLE:
            sample_df = source_payload.copy()
            if parsed_mode == PrivacyMode.STRICT:
                sample_df = _drop_identifier_columns(sample_df)
            sample_limit = _sample_limit(parsed_mode)
            sample = sample_df.head(sample_limit).to_dict(orient="records")
            context["sample_row_count"] = len(sample)
            context["sample_rows"] = sample
        return context

    # text / markdown
    context["profile"] = profile
    if parsed_scope == ContextScope.SCHEMA_STATS_SAMPLE:
        lines = str(source_payload).splitlines()
        sample_limit = _sample_limit(parsed_mode)
        context["sample_row_count"] = min(sample_limit, len(lines))
        context["sample_rows"] = lines[:sample_limit]
    return context

