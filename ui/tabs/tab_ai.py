# -*- coding: utf-8 -*-
"""AI Chat tab: context selection, anonymization handling, and Mistral chat."""

from __future__ import annotations

import logging
import os

import streamlit as st

from core.file_ops import create_anonymized, ensure_file_context, file_kind
from llm.context_builder import ContextScope, build_context
from llm.mistral_client import send_to_mistral
from llm.send_guard import dispatch_ai_send
from privacy.pii_detector import PrivacyMode
from ui.i18n import t
from ui.pii_widgets import display_chat_history
from utils.cache import anonymized_cache_key

logger = logging.getLogger(__name__)


def _handle_anonymization(
    selected_file: str,
    payload: object,
    pii_report: object,
    anonymized_key: str,
    parsed_mode: PrivacyMode,
    success_text: str,
    button_key: str,
) -> object | None:
    """Create anonymized result on button click and store in session cache."""
    anonymized_result = st.session_state["anonymized_payloads"].get(anonymized_key)
    if anonymized_result is None:
        if st.button(t("anonymize_continue") if "continue" in button_key else t("create_anonymized_version"), key=button_key):
            anonymized_result = create_anonymized(selected_file, payload, pii_report)
            st.session_state["anonymized_payloads"][anonymized_key] = anonymized_result
            logger.info(
                "anonymization_completed file=%s mode=%s replaced_counts=%s",
                selected_file,
                parsed_mode.value,
                anonymized_result.replaced_counts,
            )
            st.success(success_text)
    return anonymized_result


def _history_newest_first_with_user_first(history: list[dict[str, str]]) -> list[dict[str, str]]:
    """Show newest turns first while keeping each user prompt above AI replies."""
    turns: list[list[dict[str, str]]] = []
    for message in history:
        if message.get("role") == "user" or not turns:
            turns.append([message])
        else:
            turns[-1].append(message)

    ordered: list[dict[str, str]] = []
    for turn in reversed(turns):
        ordered.extend(turn)
    return ordered


def render_tab_ai(selected_file: str, parsed_mode: PrivacyMode) -> None:
    if not selected_file:
        st.info(t("pick_file_hint"))
        return

    payload, profile, pii_report, effective_report = ensure_file_context(selected_file, parsed_mode.value)

    anonymized_key = anonymized_cache_key(selected_file, parsed_mode.value)
    anonymized_result = st.session_state["anonymized_payloads"].get(anonymized_key)

    if parsed_mode == PrivacyMode.RELAXED:
        st.warning(t("relaxed_warning"))

    pii_state = "detected" if effective_report.has_pii else "none"
    st.caption(t("pii_badge", state=pii_state))

    scope_map = {
        t("ctx_schema_only"): ContextScope.SCHEMA.value,
        t("ctx_schema_stats"): ContextScope.SCHEMA_STATS.value,
        t("ctx_schema_stats_sample"): ContextScope.SCHEMA_STATS_SAMPLE.value,
    }
    scope_label = st.selectbox(t("ai_context"), options=list(scope_map.keys()), index=1)
    scope_value = scope_map[scope_label]
    st.caption(t("ai_context_badge", scope=scope_value))

    if effective_report.has_pii:
        st.error(t("pii_file_error"))
        source_value = t("anonymized_version")
        anonymized_result = _handle_anonymization(
            selected_file, payload, effective_report, anonymized_key, parsed_mode,
            success_text=t("anonymization_done_continue"),
            button_key="ai_anonymize_continue",
        )
    else:
        source_options = [t("original_version"), t("anonymized_version")]
        source_value = st.radio(t("use_for_ai"), source_options, index=0)
        if source_value == t("anonymized_version"):
            anonymized_result = _handle_anonymization(
                selected_file, payload, pii_report, anonymized_key, parsed_mode,
                success_text=t("anonymization_done"),
                button_key="ai_create_anonymized",
            )

    prompt = st.text_area(t("ai_prompt"), height=120, placeholder=t("ai_prompt_placeholder"))
    display_chat_history(_history_newest_first_with_user_first(st.session_state["chat_history"]))
    send_clicked = st.button(t("send_to_ai"), type="primary")

    use_anonymized = source_value == t("anonymized_version")
    if send_clicked and use_anonymized and anonymized_result is None:
        st.error(t("create_anonymized_first"))
        return

    source_payload = payload
    if use_anonymized and anonymized_result is not None:
        source_payload = (
            anonymized_result.anonymized_df
            if anonymized_result.anonymized_df is not None
            else anonymized_result.anonymized_text
        )

    def _sender() -> str:
        context_payload = build_context(
            file_kind=file_kind(selected_file),
            profile=profile,
            source_payload=source_payload,
            mode=parsed_mode.value,
            scope=scope_value,
        )
        api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        result = send_to_mistral(
            prompt=prompt,
            context_payload=context_payload,
            api_key=api_key,
            model="mistral-small-latest",
        )
        logger.info(
            "ai_send scope=%s sample_rows=%s pii_present=%s privacy_mode=%s source=%s",
            scope_value,
            context_payload.get("sample_row_count", 0),
            effective_report.has_pii,
            parsed_mode.value,
            source_value,
        )
        return result

    try:
        reply, reason = dispatch_ai_send(
            submit_clicked=send_clicked,
            prompt=prompt,
            pii_present=effective_report.has_pii,
            use_anonymized=use_anonymized,
            sender=_sender,
        )
        if reason == "empty_prompt":
            st.error(t("empty_prompt_error"))
        elif reason == "pii_requires_anonymization":
            st.error(t("pii_requires_anonymized_error"))
        elif reason == "ok" and reply is not None:
            st.session_state["chat_history"].append({"role": "user", "content": prompt.strip()})
            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()
    except Exception as exc:
        logger.info("ai_send_failed reason=%s", str(exc))
        st.error(t("ai_send_failed", error=exc))
