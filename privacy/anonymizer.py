"""Offline anonymization based on detected PII matches."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from privacy.pii_detector import PiiReport

TOKEN_PREFIX = {
    "EMAIL": "EMAIL",
    "PHONE": "PHONE",
    "NAME": "NAME",
    "ADDRESS": "ADDRESS",
    "DOB": "DOB",
    "RC": "RC",
    "BANK": "BANK",
}


@dataclass
class AnonymizationResult:
    anonymized_df: pd.DataFrame | None = None
    anonymized_text: str | None = None
    token_maps: dict[str, dict[str, str]] = field(default_factory=dict)
    replaced_counts: dict[str, int] = field(default_factory=dict)


def _next_token(pii_type: str, counters: dict[str, int]) -> str:
    prefix = TOKEN_PREFIX.get(pii_type, pii_type.upper())
    counters[prefix] = counters.get(prefix, 0) + 1
    return f"{prefix}_{counters[prefix]}"


def anonymize_csv(df: pd.DataFrame, pii_report: PiiReport) -> AnonymizationResult:
    """Anonymize dataframe values flagged by PII report."""
    anonymized = df.copy()
    token_maps: dict[str, dict[str, str]] = {}
    counters: dict[str, int] = {}
    replaced_counts: dict[str, int] = {}
    visited: set[tuple[int, str, str]] = set()

    for match in pii_report.matches:
        key = (match.row_idx, match.column, match.pii_type)
        if key in visited:
            continue
        visited.add(key)

        if match.column not in anonymized.columns:
            continue
        if not (0 <= match.row_idx < len(anonymized)):
            continue

        raw_value = str(anonymized.iloc[match.row_idx][match.column])
        pii_type = match.pii_type
        token_maps.setdefault(pii_type, {})
        if raw_value not in token_maps[pii_type]:
            token_maps[pii_type][raw_value] = _next_token(pii_type, counters)
        token = token_maps[pii_type][raw_value]
        anonymized.at[match.row_idx, match.column] = token
        replaced_counts[pii_type] = replaced_counts.get(pii_type, 0) + 1

    return AnonymizationResult(
        anonymized_df=anonymized,
        token_maps=token_maps,
        replaced_counts=replaced_counts,
    )


def anonymize_text(text: str, pii_report: PiiReport) -> AnonymizationResult:
    """Anonymize text values flagged by PII report."""
    anonymized = text
    token_maps: dict[str, dict[str, str]] = {}
    counters: dict[str, int] = {}
    replaced_counts: dict[str, int] = {}

    pairs: list[tuple[str, str]] = []
    for match in pii_report.matches:
        if not match.raw_value:
            continue
        pairs.append((match.pii_type, match.raw_value))

    # Replace longer values first to avoid partial token collisions.
    pairs.sort(key=lambda item: len(item[1]), reverse=True)

    for pii_type, raw in pairs:
        token_maps.setdefault(pii_type, {})
        if raw not in token_maps[pii_type]:
            token_maps[pii_type][raw] = _next_token(pii_type, counters)
        token = token_maps[pii_type][raw]
        anonymized, count = re.subn(re.escape(raw), token, anonymized)
        if count:
            replaced_counts[pii_type] = replaced_counts.get(pii_type, 0) + count

    return AnonymizationResult(
        anonymized_text=anonymized,
        token_maps=token_maps,
        replaced_counts=replaced_counts,
    )

