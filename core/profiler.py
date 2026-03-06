"""Offline profiling for CSV/TXT/MD files."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

import pandas as pd

STOPWORDS_CS = {
    "a",
    "aby",
    "ale",
    "ani",
    "by",
    "co",
    "do",
    "i",
    "jako",
    "je",
    "jsou",
    "k",
    "na",
    "ne",
    "nebo",
    "se",
    "si",
    "s",
    "to",
    "u",
    "v",
    "ve",
    "z",
    "za",
    "ze",
}


def profile_csv(df: pd.DataFrame) -> dict[str, Any]:
    """Build offline profile for dataframe."""
    schema = [{"column": col, "dtype": str(df[col].dtype)} for col in df.columns]
    missing_by_column = df.isna().sum().to_dict()

    numeric_stats: dict[str, dict[str, float | None]] = {}
    for col in df.select_dtypes(include=["number"]).columns:
        series = df[col].dropna()
        if series.empty:
            numeric_stats[col] = {"min": None, "max": None, "mean": None, "median": None}
        else:
            numeric_stats[col] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "median": float(series.median()),
            }

    top_values: dict[str, list[dict[str, Any]]] = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        counts = df[col].astype(str).value_counts(dropna=True).head(5)
        top_values[col] = [{"value": idx, "count": int(value)} for idx, value in counts.items()]

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "schema": schema,
        "missing_by_column": missing_by_column,
        "numeric_stats": numeric_stats,
        "top_values": top_values,
        "duplicate_rows": int(df.duplicated().sum()),
    }


def profile_text(text: str) -> dict[str, Any]:
    """Build offline profile for text payload."""
    lines = text.splitlines()
    words = re.findall(r"\b[\wÀ-ž]+\b", text.lower())
    filtered = [word for word in words if word not in STOPWORDS_CS and len(word) > 2]
    keywords = Counter(filtered).most_common(15)

    return {
        "char_count": len(text),
        "line_count": len(lines),
        "word_count": len(words),
        "keywords": [{"term": term, "count": count} for term, count in keywords],
    }

