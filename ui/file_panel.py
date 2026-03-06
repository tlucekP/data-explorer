# -*- coding: utf-8 -*-
"""File panel: file list rendering and filter controls."""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Any

import streamlit as st

from core.file_ops import format_size
from core.indexer import list_supported_files
from ui.i18n import t
from utils.pii_state import clear_file_dependent_state, ensure_safe_scope, reset_pii_safe_overrides

logger = logging.getLogger(__name__)


def _render_file_list(entries: list[dict[str, Any]], selected_file: str) -> None:
    st.caption(t("filtered_files", count=len(entries)))
    with st.container(key="file_list_scroll"):
        if not entries:
            st.info(t("no_files_filtered"))
            return

        for idx, item in enumerate(entries):
            file_path = item["path"]
            is_active = file_path == selected_file
            if st.button(
                item["name"],
                key=f"file_pick_{idx}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if st.session_state.get("selected_file") != file_path:
                    reset_pii_safe_overrides("file_switch")
                st.session_state["selected_file"] = file_path
                logger.info("file_selected path=%s", file_path)
                st.rerun()
            st.caption(f"{format_size(item['size_bytes'])} · {item['modified_at']:%Y-%m-%d %H:%M}")


def render_file_panel(root_path: str, search: str) -> str:
    """Render the file panel shell with list and filters. Returns selected_file path."""
    with st.container(key="file_panel_shell"):
        st.markdown(f"### {t('files')}")

        default_types = [".csv", ".txt", ".md"]
        selected_types_state = st.session_state.get("panel_file_types", default_types)
        selected_types = selected_types_state if selected_types_state else default_types

        use_size_filter = bool(st.session_state.get("panel_use_size_filter", False))
        size_range = None
        if use_size_filter:
            min_kb_state = int(st.session_state.get("panel_min_size_kb", 0))
            max_kb_state = int(st.session_state.get("panel_max_size_kb", 10240))
            size_range = (int(min_kb_state * 1024), int(max_kb_state * 1024))

        use_date_filter = bool(st.session_state.get("panel_use_date_filter", False))
        modified_range = None
        if use_date_filter:
            date_from_state = st.session_state.get("panel_date_from", datetime.now().date())
            date_to_state = st.session_state.get("panel_date_to", datetime.now().date())
            if date_from_state > date_to_state:
                date_from_state, date_to_state = date_to_state, date_from_state
            modified_range = (
                datetime.combine(date_from_state, time.min),
                datetime.combine(date_to_state, time.max),
            )

        scan_signature = (
            root_path,
            tuple(sorted(selected_types)),
            search,
            size_range,
            modified_range,
        )
        if st.session_state.get("last_scan_signature") != scan_signature:
            clear_file_dependent_state()
            st.session_state["last_scan_signature"] = scan_signature

        entries = list_supported_files(
            root_path=root_path,
            recursive=True,
            search=search,
            file_types=selected_types,
            size_range=size_range,
            modified_range=modified_range,
        )

        valid_paths = {item["path"] for item in entries}
        if st.session_state["selected_file"] not in valid_paths:
            st.session_state["selected_file"] = ""
            reset_pii_safe_overrides("file_not_in_scope")
        selected_file = st.session_state["selected_file"]
        ensure_safe_scope(selected_file)

        _render_file_list(entries, selected_file)

        with st.container(key="file_panel_filter_wrap", height="stretch"):
            st.caption(t("file_filters"))
            st.multiselect(
                t("file_type"),
                [".csv", ".txt", ".md"],
                default=default_types,
                key="panel_file_types",
            )
            use_size_filter_ui = st.checkbox(t("filter_size"), key="panel_use_size_filter")
            if use_size_filter_ui:
                st.number_input(t("min_size"), min_value=0, value=0, step=1, key="panel_min_size_kb")
                st.number_input(t("max_size"), min_value=0, value=10240, step=10, key="panel_max_size_kb")
            use_date_filter_ui = st.checkbox(t("filter_date"), key="panel_use_date_filter")
            if use_date_filter_ui:
                st.date_input(t("date_from"), key="panel_date_from")
                st.date_input(t("date_to"), key="panel_date_to")
            if st.button(t("reload_list"), key="panel_reload_list"):
                clear_file_dependent_state()
                st.session_state["last_scan_signature"] = None
            st.caption(t("found_files", count=len(entries)))

    return selected_file
