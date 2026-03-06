"""Session cache helpers."""

from __future__ import annotations

from typing import Any, MutableMapping


def ensure_session_defaults(session_state: MutableMapping[str, Any]) -> None:
    defaults = {
        "root_path": "",
        "selected_file": "",
        "last_scan_signature": None,
        "pii_reveal_key": None,
        "pii_reveal_until_ts": None,
        "pii_safe_match_keys": [],
        "pii_safe_for_file": "",
        "last_privacy_mode": None,
        "profiles": {},
        "file_payloads": {},
        "pii_reports": {},
        "anonymized_payloads": {},
        "chat_history": [],
        "context_scope": "schema+stats",
        "ui_lang": "cs",
        "last_root_path_value": "",
    }
    for key, value in defaults.items():
        if key not in session_state:
            session_state[key] = value


def pii_cache_key(file_path: str, mode: str) -> str:
    return f"{mode}::{file_path}"


def anonymized_cache_key(file_path: str, mode: str) -> str:
    return f"{mode}::{file_path}"
