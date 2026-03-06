# -*- coding: utf-8 -*-
"""Logs tab: display application log files."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ui.i18n import t


def render_tab_logs() -> None:
    logs_parts: list[str] = []
    for log_path in (Path("app.log"), Path("logs") / "app.log"):
        try:
            content = log_path.read_bytes().decode("utf-8", errors="replace")
        except (FileNotFoundError, OSError):
            content = ""
        if content.strip():
            logs_parts.append(f"=== {log_path.as_posix()} ===\n{content}")
    logs = "\n\n".join(logs_parts)
    st.text_area(t("application_logs"), logs, height=300)
