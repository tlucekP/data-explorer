# -*- coding: utf-8 -*-
"""Explore tab: offline profiling, PII report, and anonymization."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from core.file_ops import create_anonymized, ensure_file_context
from privacy.pii_detector import PrivacyMode
from ui.i18n import t
from ui.pii_widgets import render_pii_report, render_profile
from utils.cache import anonymized_cache_key

logger = logging.getLogger(__name__)


def render_tab_explore(selected_file: str, parsed_mode: PrivacyMode) -> None:
    if not selected_file:
        st.info(t("pick_file_hint"))
        return

    payload, profile, _pii_report, effective_report = ensure_file_context(selected_file, parsed_mode.value)

    st.subheader(t("offline_profiling"))
    render_profile(profile, selected_file)

    st.subheader(t("pii_report"))
    render_pii_report(effective_report, selected_file=selected_file, mode=parsed_mode.value)

    anonymized_key = anonymized_cache_key(selected_file, parsed_mode.value)
    anonymized_result = st.session_state["anonymized_payloads"].get(anonymized_key)

    if effective_report.has_pii:
        st.warning(t("pii_found_warning"))
        if st.button(t("anonymize_for_ai"), type="primary"):
            anonymized_result = create_anonymized(selected_file, payload, effective_report)
            st.session_state["anonymized_payloads"][anonymized_key] = anonymized_result
            logger.info(
                "anonymization_completed file=%s mode=%s replaced_counts=%s",
                selected_file,
                parsed_mode.value,
                anonymized_result.replaced_counts,
            )
            st.success(t("anonymized_created"))

    if anonymized_result:
        st.subheader(t("anonymized_variant"))
        if anonymized_result.anonymized_df is not None:
            st.dataframe(anonymized_result.anonymized_df.head(20), use_container_width=True)
            file_name = f"{Path(selected_file).stem}_anonymized.csv"
            csv_bytes = anonymized_result.anonymized_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("export_anonymized_csv"),
                data=csv_bytes,
                file_name=file_name,
                mime="text/csv",
            )
        elif anonymized_result.anonymized_text is not None:
            st.text(anonymized_result.anonymized_text[:5000])
