"""Masking helpers for safe PII previews in UI."""

from __future__ import annotations

import re


def _mask_email(value: str) -> str:
    if "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    local_mask = (local[:2] + "***") if len(local) >= 2 else "***"
    if "." in domain:
        d1, d2 = domain.split(".", 1)
        d1_mask = (d1[:2] + "***") if len(d1) >= 2 else "***"
        return f"{local_mask}@{d1_mask}.{d2}"
    return f"{local_mask}@***"


def _mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not digits:
        return "***"
    prefix = "+420 " if value.strip().startswith("+") else ""
    return f"{prefix}*** *** ***"


def _mask_generic(value: str) -> str:
    text = value.strip()
    if len(text) <= 2:
        return "*" * len(text)
    return f"{text[:1]}***{text[-1:]}"


def mask_value(value: str, pii_type: str) -> str:
    """Return masked preview suitable for UI display."""
    text = str(value or "")
    pii = pii_type.upper()
    if pii == "EMAIL":
        return _mask_email(text)
    if pii == "PHONE":
        return _mask_phone(text)
    return _mask_generic(text)

