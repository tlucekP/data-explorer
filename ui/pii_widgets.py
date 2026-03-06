# -*- coding: utf-8 -*-
"""UI widgets for profile rendering, PII report display, and chat history."""

from __future__ import annotations

import logging
import time as pytime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from core.file_ops import file_kind
from privacy.pii_detector import PiiReport, PrivacyMode, parse_mode
from ui.i18n import t
from utils.pii_state import (
    build_pii_reveal_key,
    reset_pii_reveal,
    reset_pii_safe_overrides,
    safe_match_keys,
    save_safe_match_keys,
)

logger = logging.getLogger(__name__)


def render_profile(profile: dict[str, Any], file_path: str) -> None:
    if file_kind(file_path) == "csv":
        c1, c2, c3 = st.columns(3)
        c1.metric(t("rows_count"), profile.get("row_count", 0))
        c2.metric(t("columns_count"), profile.get("column_count", 0))
        c3.metric(t("duplicate_rows"), profile.get("duplicate_rows", 0))

        st.subheader(t("schema"))
        st.dataframe(pd.DataFrame(profile.get("schema", [])), use_container_width=True)

        st.subheader(t("missing_values"))
        missing_df = pd.DataFrame(
            [{"column": key, "missing": value} for key, value in profile.get("missing_by_column", {}).items()]
        )
        st.dataframe(missing_df, use_container_width=True)

        st.subheader(t("numeric_stats"))
        numeric_stats = profile.get("numeric_stats", {})
        if numeric_stats:
            stats_rows = [{"column": key, **value} for key, value in numeric_stats.items()]
            st.dataframe(pd.DataFrame(stats_rows), use_container_width=True)
        else:
            st.info(t("no_numeric_columns"))

        st.subheader(t("top_values"))
        top_values = profile.get("top_values", {})
        if not top_values:
            st.info(t("no_top_values"))
        for column, values in top_values.items():
            with st.expander(t("column_label", column=column)):
                st.dataframe(pd.DataFrame(values), use_container_width=True)
        return

    c1, c2, c3 = st.columns(3)
    c1.metric(t("char_count"), profile.get("char_count", 0))
    c2.metric(t("line_count"), profile.get("line_count", 0))
    c3.metric(t("word_count"), profile.get("word_count", 0))
    st.subheader(t("keywords"))
    st.dataframe(pd.DataFrame(profile.get("keywords", [])), use_container_width=True)


def render_pii_report(pii_report: PiiReport, selected_file: str, mode: str) -> None:
    if not pii_report.has_pii:
        st.success(t("pii_none"))
        return

    st.error(t("pii_detected"))
    totals_df = pd.DataFrame(
        [{"pii_type": key, "count": value} for key, value in pii_report.totals_by_type.items()]
    )
    st.subheader(t("pii_summary"))
    st.dataframe(totals_df, use_container_width=True)

    matches = pii_report.matches[:200]
    st.subheader(t("masked_samples"))

    reveal_key = st.session_state.get("pii_reveal_key")
    reveal_until = st.session_state.get("pii_reveal_until_ts")
    if reveal_key and (reveal_until is None or pytime.time() > float(reveal_until)):
        reset_pii_reveal("timeout")
        reveal_key = None

    header_cols = st.columns([1, 1, 1, 1.35, 1.35, 0.75, 0.9])
    header_cols[0].markdown(f"**{t('type')}**")
    header_cols[1].markdown(f"**{t('row')}**")
    header_cols[2].markdown(f"**{t('column')}**")
    header_cols[3].markdown(f"**{t('masked_match')}**")
    header_cols[4].markdown(f"**{t('detection_rule')}**")
    header_cols[5].markdown("**confidence**")
    header_cols[6].markdown(f"**{t('action')}**")

    reveal_map: dict[str, Any] = {}
    for idx, match in enumerate(matches):
        key = build_pii_reveal_key(selected_file, mode, match)
        reveal_map[key] = match

        cols = st.columns([1, 1, 1, 1.35, 1.35, 0.75, 0.9])
        cols[0].write(match.pii_type)
        cols[1].write(match.row_idx)
        cols[2].write(match.column)
        cols[3].write(match.masked_preview)
        cols[4].write(match.source_rule)
        cols[5].write(round(match.confidence, 2))

        label = t("shown") if st.session_state.get("pii_reveal_key") == key else t("show")
        if cols[6].button(label, key=f"pii_reveal_btn_{idx}", use_container_width=True):
            st.session_state["pii_reveal_key"] = key
            st.session_state["pii_reveal_until_ts"] = pytime.time() + 30
            logger.info(
                "pii_reveal_clicked type=%s row=%s column=%s",
                match.pii_type,
                match.row_idx,
                match.column,
            )
            st.rerun()

    active_key = st.session_state.get("pii_reveal_key")
    active_until = st.session_state.get("pii_reveal_until_ts")
    if active_key and active_key not in reveal_map:
        reset_pii_reveal("context_change")
        active_key = None

    if active_key and active_key in reveal_map and active_until is not None:
        active_match = reveal_map[active_key]
        remaining = max(0, int(float(active_until) - pytime.time()))
        st.markdown(f"#### {t('finding_detail')}")
        st.warning(t("sensitive_warning"))
        st.write(t("masked_value", value=active_match.masked_preview))
        raw_value = active_match.raw_value if getattr(active_match, "raw_value", "") else t("value_unavailable")
        st.write(t("unmasked_value", value=raw_value))
        st.caption(t("auto_hide", seconds=remaining))
        action_cols = st.columns([1, 1.6, 3])
        if action_cols[0].button(t("hide"), key="pii_reveal_hide", type="secondary"):
            reset_pii_reveal("manual")
            st.rerun()
        if parse_mode(mode) == PrivacyMode.STRICT and action_cols[1].button(
            t("mark_safe"),
            key="pii_mark_safe",
            type="primary",
            use_container_width=True,
        ):
            keys = safe_match_keys()
            match_key = build_pii_reveal_key(selected_file, mode, active_match)
            keys.add(match_key)
            save_safe_match_keys(keys)
            logger.info(
                "pii_safe_marked file=%s mode=%s type=%s row=%s column=%s rule=%s",
                selected_file,
                mode,
                active_match.pii_type,
                active_match.row_idx,
                active_match.column,
                active_match.source_rule,
            )
            reset_pii_reveal("safe_marked")
            st.rerun()


def display_chat_history(history: list[dict[str, str]]) -> None:
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
