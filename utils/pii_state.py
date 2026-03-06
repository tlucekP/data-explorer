# -*- coding: utf-8 -*-
"""PII session-state management: safe-override and reveal helpers."""

from __future__ import annotations

import logging
import time as pytime
from typing import Any

import streamlit as st

from privacy.pii_detector import PiiReport, PrivacyMode, parse_mode

logger = logging.getLogger(__name__)


def build_pii_reveal_key(selected_file: str, mode: str, match: Any) -> str:
    return f"{selected_file}|{mode}|{match.row_idx}|{match.column}|{match.pii_type}|{match.source_rule}"


def safe_match_keys() -> set[str]:
    return set(st.session_state.get("pii_safe_match_keys", []))


def save_safe_match_keys(keys: set[str]) -> None:
    st.session_state["pii_safe_match_keys"] = sorted(keys)


def reset_pii_safe_overrides(reason: str, log: bool = True) -> None:
    had_safe = bool(st.session_state.get("pii_safe_match_keys"))
    st.session_state["pii_safe_match_keys"] = []
    st.session_state["pii_safe_for_file"] = ""
    if log and had_safe:
        logger.info("pii_safe_cleared reason=%s", reason)


def ensure_safe_scope(selected_file: str) -> None:
    current_file = st.session_state.get("pii_safe_for_file", "")
    if selected_file and current_file != selected_file:
        reset_pii_safe_overrides("file_change")
        st.session_state["pii_safe_for_file"] = selected_file
    elif not selected_file and current_file:
        reset_pii_safe_overrides("file_cleared")


def reset_pii_reveal(reason: str, log: bool = True) -> None:
    had_reveal = bool(st.session_state.get("pii_reveal_key"))
    st.session_state["pii_reveal_key"] = None
    st.session_state["pii_reveal_until_ts"] = None
    if log and had_reveal:
        logger.info("pii_reveal_hidden reason=%s", reason)


def report_from_matches(matches: list[Any]) -> PiiReport:
    if not matches:
        return PiiReport(has_pii=False, matches=[])

    totals: dict[str, int] = {}
    columns: dict[str, set[str]] = {}
    rows: dict[str, set[int]] = {}
    for match in matches:
        totals[match.pii_type] = totals.get(match.pii_type, 0) + 1
        columns.setdefault(match.pii_type, set()).add(match.column)
        rows.setdefault(match.pii_type, set()).add(match.row_idx)

    return PiiReport(
        has_pii=True,
        totals_by_type=totals,
        columns_by_type={key: sorted(list(value)) for key, value in columns.items()},
        row_indexes_by_type={key: sorted(list(value)) for key, value in rows.items()},
        matches=matches,
    )


def effective_pii_report(pii_report: PiiReport, selected_file: str, mode: str) -> PiiReport:
    if parse_mode(mode) != PrivacyMode.STRICT:
        return pii_report
    keys = safe_match_keys()
    if not keys:
        return pii_report

    filtered: list[Any] = [
        match for match in pii_report.matches
        if build_pii_reveal_key(selected_file, mode, match) not in keys
    ]
    return report_from_matches(filtered)


def clear_file_dependent_state() -> None:
    st.session_state["selected_file"] = ""
    st.session_state["profiles"] = {}
    st.session_state["file_payloads"] = {}
    st.session_state["pii_reports"] = {}
    st.session_state["anonymized_payloads"] = {}
    reset_pii_safe_overrides("context_change")
    reset_pii_reveal("context_change")
