# -*- coding: utf-8 -*-
"""Local Data Explorer: offline profiling + PII protection + controlled Mistral chat."""

from __future__ import annotations

import logging

import streamlit as st
from dotenv import load_dotenv

from core.file_ops import pick_folder_with_windows_dialog
from privacy.pii_detector import PrivacyMode, parse_mode
from ui.i18n import LANG_OPTIONS, t
from ui.file_panel import render_file_panel
from ui.shutdown import handle_shutdown_button
from ui.styles import render_backend_chip, render_styles
from ui.tabs.tab_ai import render_tab_ai
from ui.tabs.tab_explore import render_tab_explore
from ui.tabs.tab_logs import render_tab_logs
from utils.cache import ensure_session_defaults
from utils.logging import setup_logging
from utils.pii_state import clear_file_dependent_state, reset_pii_reveal, reset_pii_safe_overrides

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="app.log",
    filemode="a",
    encoding="utf-8",
)

load_dotenv()
logger = setup_logging()
logger.propagate = True

st.set_page_config(page_title="Data Explorer", page_icon="🔐", layout="wide")


def main() -> None:
    ensure_session_defaults(st.session_state)

    # --- Language picker ---
    lang_labels = list(LANG_OPTIONS.keys())
    current_label = next(
        (label for label, code in LANG_OPTIONS.items() if code == st.session_state.get("ui_lang", "cs")),
        lang_labels[0],
    )
    with st.sidebar.container(key="lang_picker"):
        st.markdown(
            """
            <div class="lang-flag-row">
              <span class="lang-flag-chip">
                <svg viewBox="0 0 22 14" xmlns="http://www.w3.org/2000/svg" aria-label="Czech flag">
                  <rect width="22" height="7" fill="#ffffff"/>
                  <rect y="7" width="22" height="7" fill="#d7141a"/>
                  <polygon points="0,0 10,7 0,14" fill="#11457e"/>
                </svg>
                CZE
              </span>
              <span class="lang-flag-chip">
                <svg viewBox="0 0 22 14" xmlns="http://www.w3.org/2000/svg" aria-label="UK flag">
                  <rect width="22" height="14" fill="#012169"/>
                  <polygon points="0,0 2.6,0 22,11.9 22,14 19.4,14 0,2.1" fill="#fff"/>
                  <polygon points="22,0 19.4,0 0,11.9 0,14 2.6,14 22,2.1" fill="#fff"/>
                  <polygon points="0,0 1.4,0 22,12.8 22,14 20.6,14 0,1.2" fill="#C8102E"/>
                  <polygon points="22,0 20.6,0 0,12.8 0,14 1.4,14 22,1.2" fill="#C8102E"/>
                  <rect x="9" width="4" height="14" fill="#fff"/>
                  <rect y="5" width="22" height="4" fill="#fff"/>
                  <rect x="9.7" width="2.6" height="14" fill="#C8102E"/>
                  <rect y="5.7" width="22" height="2.6" fill="#C8102E"/>
                </svg>
                ENG
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_lang_label = st.selectbox(
            t("lang_switch_label"),
            options=lang_labels,
            index=lang_labels.index(current_label),
            label_visibility="collapsed",
        )
    st.session_state["ui_lang"] = LANG_OPTIONS[selected_lang_label]

    # --- Sidebar: root folder ---
    st.sidebar.header(t("sidebar_settings"))
    if "pending_root_path_input" in st.session_state:
        st.session_state["root_path_input"] = st.session_state.pop("pending_root_path_input")
    if "root_path_input" not in st.session_state:
        st.session_state["root_path_input"] = st.session_state.get("root_path", "")
    root_path = st.sidebar.text_input(t("root_folder"), key="root_path_input")

    if st.sidebar.button(t("pick_folder_button")):
        selected_dir = pick_folder_with_windows_dialog(root_path, t("folder_picker_title"))
        if selected_dir:
            st.session_state["root_path"] = selected_dir
            st.session_state["pending_root_path_input"] = selected_dir
            clear_file_dependent_state()
            st.session_state["last_scan_signature"] = None
            st.session_state["last_root_path_value"] = selected_dir
            st.rerun()
        else:
            st.sidebar.info(t("folder_picker_cancelled"))

    st.session_state["root_path"] = root_path

    if root_path != st.session_state.get("last_root_path_value"):
        clear_file_dependent_state()
        st.session_state["last_scan_signature"] = None
        st.session_state["last_root_path_value"] = root_path

    # --- Sidebar: privacy mode ---
    mode_options = [PrivacyMode.STRICT.value, PrivacyMode.BALANCED.value, PrivacyMode.RELAXED.value]
    privacy_mode = st.sidebar.selectbox(t("privacy_mode"), options=mode_options, index=0)
    parsed_mode = parse_mode(privacy_mode)
    if st.session_state.get("last_privacy_mode") != parsed_mode.value:
        reset_pii_safe_overrides("mode_change")
        reset_pii_reveal("context_change")
        st.session_state["last_privacy_mode"] = parsed_mode.value

    if parsed_mode == PrivacyMode.STRICT:
        st.sidebar.info(t("strict_info"))
    elif parsed_mode == PrivacyMode.BALANCED:
        st.sidebar.info(t("balanced_info"))
    else:
        st.sidebar.warning(t("relaxed_warning"))

    # --- Sidebar: backend animation style ---
    anim_style_options = {
        t("backend_anim_pulse"): "pulse",
        t("backend_anim_orbit"): "orbit",
        t("backend_anim_bars"): "bars",
    }
    selected_anim_label = st.sidebar.selectbox(
        t("backend_anim_catalog"),
        options=list(anim_style_options.keys()),
        index=0,
        help=t("backend_anim_help"),
    )
    backend_anim_style = anim_style_options[selected_anim_label]

    search = st.sidebar.text_input(t("search_name"))

    # --- Global UI elements ---
    render_styles()
    render_backend_chip(backend_anim_style)
    handle_shutdown_button()

    # --- Main layout ---
    with st.container(key="workspace_layout"):
        file_panel_col, content_col = st.columns([1, 3], gap="small")
        with file_panel_col:
            selected_file = render_file_panel(root_path, search)

        with content_col:
            st.title(t("app_title"))
            st.caption(t("app_caption"))

            tab_explore, tab_ai, tab_logs = st.tabs([t("tab_explore"), t("tab_ai_chat"), t("tab_logs")])
            with tab_explore:
                render_tab_explore(selected_file, parsed_mode)
            with tab_ai:
                render_tab_ai(selected_file, parsed_mode)
            with tab_logs:
                render_tab_logs()


if __name__ == "__main__":
    main()
