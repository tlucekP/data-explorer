# -*- coding: utf-8 -*-
"""File loading, dispatch helpers, and session-cached file context."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from core.profiler import profile_csv, profile_text
from privacy.anonymizer import AnonymizationResult, anonymize_csv, anonymize_text
from privacy.pii_detector import PiiReport, detect_csv_pii, detect_text_pii
from utils.cache import anonymized_cache_key, pii_cache_key
from utils.pii_state import effective_pii_report

logger = logging.getLogger(__name__)


def format_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def file_kind(file_path: str) -> str:
    return "csv" if Path(file_path).suffix.lower() == ".csv" else "text"


def load_csv(file_path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.read_csv(file_path, sep=None, engine="python")


def load_payload(file_path: str) -> Any:
    if file_kind(file_path) == "csv":
        return load_csv(file_path).reset_index(drop=True)
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")


def pick_folder_with_windows_dialog(initial_dir: str, dialog_title: str) -> str:
    """Open native Windows folder picker and return selected path or empty string."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(
            title=dialog_title,
            initialdir=initial_dir if Path(initial_dir).exists() else str(Path.home()),
        )
        root.destroy()
        return selected or ""
    except Exception as exc:
        logger.info("folder_picker_failed reason=%s", str(exc))
        return ""


def profile_payload(file_path: str, payload: Any) -> dict[str, Any]:
    if file_kind(file_path) == "csv":
        return profile_csv(payload)
    return profile_text(payload)


def detect_pii(file_path: str, payload: Any, mode: str) -> Any:
    if file_kind(file_path) == "csv":
        return detect_csv_pii(payload, mode=mode)
    return detect_text_pii(payload, mode=mode)


def create_anonymized(file_path: str, payload: Any, pii_report: Any) -> AnonymizationResult:
    if file_kind(file_path) == "csv":
        return anonymize_csv(payload, pii_report)
    return anonymize_text(payload, pii_report)


def ensure_file_context(
    selected_file: str, parsed_mode_value: str
) -> tuple[Any, dict[str, Any], PiiReport, PiiReport]:
    """Load payload, profile and PII report from session cache (or compute).

    Returns: (payload, profile, pii_report, effective_report)
    """
    if selected_file not in st.session_state["file_payloads"]:
        st.session_state["file_payloads"][selected_file] = load_payload(selected_file)
        logger.info("file_loaded file=%s", selected_file)

    payload = st.session_state["file_payloads"][selected_file]

    profile = st.session_state["profiles"].get(selected_file)
    if profile is None:
        profile = profile_payload(selected_file, payload)
        st.session_state["profiles"][selected_file] = profile
        logger.info("profiling_completed file=%s kind=%s", selected_file, file_kind(selected_file))

    report_key = pii_cache_key(selected_file, parsed_mode_value)
    pii_report = st.session_state["pii_reports"].get(report_key)
    if pii_report is None:
        pii_report = detect_pii(selected_file, payload, parsed_mode_value)
        st.session_state["pii_reports"][report_key] = pii_report
        logger.info(
            "pii_detection file=%s mode=%s has_pii=%s totals=%s",
            selected_file,
            parsed_mode_value,
            pii_report.has_pii,
            pii_report.totals_by_type,
        )

    eff_report = effective_pii_report(pii_report, selected_file, parsed_mode_value)
    return payload, profile, pii_report, eff_report
