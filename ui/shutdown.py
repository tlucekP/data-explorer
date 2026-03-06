# -*- coding: utf-8 -*-
"""App shutdown sequence: state cleanup, overlay, and process exit."""

from __future__ import annotations

import logging
import os
import threading
import time as pytime

import streamlit as st
import streamlit.components.v1 as components

from ui.i18n import t
from utils.pii_state import clear_file_dependent_state

logger = logging.getLogger(__name__)


def _schedule_app_shutdown() -> None:
    def _shutdown() -> None:
        pytime.sleep(1.2)
        os._exit(0)

    threading.Thread(target=_shutdown, daemon=True).start()


def _clear_runtime_state_on_shutdown() -> None:
    clear_file_dependent_state()
    st.session_state["root_path"] = ""
    st.session_state["pending_root_path_input"] = ""
    st.session_state["last_scan_signature"] = None
    st.session_state["last_root_path_value"] = ""
    st.session_state["chat_history"] = []


def _render_shutdown_screen(message: str) -> None:
    safe_message = (
        message.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
    components.html(
        f"""
        <script>
        (function() {{
            try {{
                var doc = window.parent.document;
                var existing = doc.getElementById("app-shutdown-overlay");
                if (existing) {{
                    existing.remove();
                }}
                var overlay = doc.createElement("div");
                overlay.id = "app-shutdown-overlay";
                overlay.style.position = "fixed";
                overlay.style.inset = "0";
                overlay.style.zIndex = "2147483647";
                overlay.style.display = "grid";
                overlay.style.placeItems = "center";
                overlay.style.background = "#020817";
                overlay.style.color = "#e2e8f0";
                overlay.style.fontFamily = "Segoe UI, Arial, sans-serif";
                overlay.innerHTML = '<div style="max-width:760px;margin:24px;padding:22px 24px;border-radius:12px;border:1px solid #334155;background:#0f172a;font-size:18px;line-height:1.45;text-align:center;">{safe_message}</div>';
                doc.body.appendChild(overlay);
                setTimeout(function() {{
                    try {{ window.top.open('', '_self'); window.top.close(); }} catch (e) {{}}
                }}, 120);
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def handle_shutdown_button() -> None:
    if st.button(t("exit_app"), key="exit_app_action"):
        logger.info("app_shutdown_requested")
        _clear_runtime_state_on_shutdown()
        _render_shutdown_screen(t("exit_app_message"))
        _schedule_app_shutdown()
        st.stop()
