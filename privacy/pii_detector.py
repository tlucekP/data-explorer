"""Offline PII detection with privacy modes."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

import pandas as pd

from utils.masking import mask_value

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,3}\)?[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{3}\b"
)
DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
]
RC_PATTERN = re.compile(r"\b\d{2}[0-1]\d[0-3]\d/?\d{3,4}\b")
BANK_ACCOUNT_PATTERN = re.compile(r"\b(?:\d{0,6}-)?\d{2,10}/\d{4}\b")
IBAN_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.IGNORECASE)
CZ_IBAN_PATTERN = re.compile(r"\bCZ\d{22}\b", re.IGNORECASE)
POSTCODE_PATTERN = re.compile(r"\b\d{3}\s?\d{2}\b")

NAME_KEYS = {
    "name",
    "first_name",
    "last_name",
    "surname",
    "given_name",
    "family_name",
    "full_name",
    "jmeno",
    "prijmeni",
    "cele_jmeno",
}
ADDRESS_KEYS = {
    "address",
    "street",
    "ulice",
    "city",
    "mesto",
    "psc",
    "zip",
    "postal",
    "house",
    "house_number",
    "cp",
    "co",
}
RC_KEYS = {"rodne_cislo", "rc"}
DOB_HINT_KEYS = {"birth", "dob", "date_of_birth", "narozeni"}
TIMESTAMP_WHITELIST_KEYS = {"created_at", "updated_at", "timestamp", "created", "modified"}
ADDRESS_HINTS = ("ul.", "třída", "trida", "náměstí", "namesti", "č.p.", "c.p.", "č.o.", "c.o.")


class PrivacyMode(str, Enum):
    STRICT = "Strict"
    BALANCED = "Balanced"
    RELAXED = "Relaxed"


@dataclass
class PiiMatch:
    pii_type: str
    row_idx: int
    column: str
    masked_preview: str
    confidence: float
    source_rule: str
    raw_value: str = ""


@dataclass
class PiiReport:
    has_pii: bool
    totals_by_type: dict[str, int] = field(default_factory=dict)
    columns_by_type: dict[str, list[str]] = field(default_factory=dict)
    row_indexes_by_type: dict[str, list[int]] = field(default_factory=dict)
    matches: list[PiiMatch] = field(default_factory=list)


def parse_mode(mode: str | PrivacyMode) -> PrivacyMode:
    if isinstance(mode, PrivacyMode):
        return mode
    normalized = str(mode or "").strip().lower()
    if normalized == "balanced":
        return PrivacyMode.BALANCED
    if normalized == "relaxed":
        return PrivacyMode.RELAXED
    return PrivacyMode.STRICT


def _normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def _parse_date(text: str) -> date | None:
    candidates = (
        ("%Y-%m-%d", text),
        ("%d.%m.%Y", text),
        ("%d/%m/%Y", text),
    )
    for fmt, value in candidates:
        try:
            parsed = datetime.strptime(value, fmt).date()
            if 1900 <= parsed.year <= date.today().year and parsed <= date.today():
                return parsed
        except ValueError:
            continue
    return None


def _valid_phone(text: str) -> bool:
    digits = re.sub(r"\D", "", text)
    return 9 <= len(digits) <= 15


def _is_dob_hint_column(normalized_col: str) -> bool:
    if normalized_col in DOB_HINT_KEYS:
        return True
    tokens = [token for token in normalized_col.split("_") if token]
    if "dob" in tokens or "birth" in tokens:
        return True
    if "narozeni" in normalized_col:
        return True
    return False


def _valid_rc(value: str) -> bool:
    normalized = value.replace("/", "")
    if len(normalized) not in (9, 10) or not normalized.isdigit():
        return False

    yy = int(normalized[0:2])
    mm = int(normalized[2:4])
    dd = int(normalized[4:6])

    if mm > 70:
        mm -= 70
    elif mm > 50:
        mm -= 50
    elif mm > 20:
        mm -= 20

    current_two_digits = date.today().year % 100
    year = 2000 + yy if yy <= current_two_digits else 1900 + yy

    try:
        datetime(year, mm, dd)
    except ValueError:
        return False

    if len(normalized) == 10 and int(normalized) % 11 != 0:
        return False
    return True


def _new_match(
    pii_type: str,
    row_idx: int,
    column: str,
    raw_value: str,
    confidence: float,
    source_rule: str,
) -> PiiMatch:
    return PiiMatch(
        pii_type=pii_type,
        row_idx=row_idx,
        column=column,
        masked_preview=mask_value(raw_value, pii_type),
        confidence=confidence,
        source_rule=source_rule,
        raw_value=raw_value,
    )


def _report_from_matches(matches: list[PiiMatch]) -> PiiReport:
    if not matches:
        return PiiReport(has_pii=False, matches=[])

    totals: dict[str, int] = {}
    columns: dict[str, set[str]] = {}
    rows: dict[str, set[int]] = {}
    for match in matches:
        totals[match.pii_type] = totals.get(match.pii_type, 0) + 1
        columns.setdefault(match.pii_type, set()).add(match.column)
        rows.setdefault(match.pii_type, set()).add(match.row_idx)

    return PiiReport(
        has_pii=True,
        totals_by_type=totals,
        columns_by_type={key: sorted(list(value)) for key, value in columns.items()},
        row_indexes_by_type={key: sorted(list(value)) for key, value in rows.items()},
        matches=matches,
    )


def _collect_line_matches(line: str, line_idx: int, mode: PrivacyMode) -> list[PiiMatch]:
    results: list[PiiMatch] = []
    for pattern, pii_type, confidence in (
        (EMAIL_PATTERN, "EMAIL", 0.99),
        (PHONE_PATTERN, "PHONE", 0.9),
        (RC_PATTERN, "RC", 0.9),
        (BANK_ACCOUNT_PATTERN, "BANK", 0.9),
        (IBAN_PATTERN, "BANK", 0.9),
    ):
        for item in pattern.findall(line):
            if pii_type == "PHONE" and not _valid_phone(item):
                continue
            if pii_type == "RC" and mode in (PrivacyMode.STRICT, PrivacyMode.BALANCED) and not _valid_rc(item):
                continue
            results.append(_new_match(pii_type, line_idx, "text", item, confidence, "regex_text"))

    for date_pattern in DATE_PATTERNS:
        for item in date_pattern.findall(line):
            parsed = _parse_date(item)
            if parsed and parsed.year < date.today().year - 10:
                results.append(_new_match("DOB", line_idx, "text", item, 0.85, "regex_date_text"))

    if mode in (PrivacyMode.STRICT, PrivacyMode.BALANCED):
        lowered = line.lower()
        if any(hint in lowered for hint in ADDRESS_HINTS):
            results.append(_new_match("ADDRESS", line_idx, "text", line.strip()[:80], 0.6, "address_hint_text"))

    return results


def detect_text_pii(text: str, mode: str | PrivacyMode) -> PiiReport:
    """Detect PII in plain text."""
    parsed_mode = parse_mode(mode)
    matches: list[PiiMatch] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        matches.extend(_collect_line_matches(line, idx, parsed_mode))
    return _report_from_matches(matches)


def detect_csv_pii(df: pd.DataFrame, mode: str | PrivacyMode) -> PiiReport:
    """Detect PII in dataframe using regex and heuristics."""
    parsed_mode = parse_mode(mode)
    matches: list[PiiMatch] = []

    for column in df.columns:
        col = str(column)
        normalized_col = _normalize_name(col)
        is_name_col = normalized_col in NAME_KEYS
        is_address_col = normalized_col in ADDRESS_KEYS
        is_rc_col = normalized_col in RC_KEYS
        is_dob_hint_col = _is_dob_hint_column(normalized_col)
        is_timestamp_col = normalized_col in TIMESTAMP_WHITELIST_KEYS

        for row_idx, value in enumerate(df[col].tolist()):
            if pd.isna(value):
                continue
            raw = str(value).strip()
            if not raw:
                continue

            cell_detections: dict[str, PiiMatch] = {}

            if EMAIL_PATTERN.search(raw):
                cell_detections["EMAIL"] = _new_match("EMAIL", row_idx, col, raw, 0.99, "regex_email")

            phone_match = PHONE_PATTERN.search(raw)
            if phone_match and _valid_phone(raw):
                cell_detections["PHONE"] = _new_match("PHONE", row_idx, col, raw, 0.9, "regex_phone")

            parsed_date: date | None = None
            for pattern in DATE_PATTERNS:
                if pattern.search(raw):
                    parsed_date = _parse_date(raw)
                    if parsed_date:
                        break
            if parsed_date and not is_timestamp_col:
                if is_dob_hint_col or parsed_date.year < date.today().year - 10:
                    cell_detections["DOB"] = _new_match("DOB", row_idx, col, raw, 0.88, "regex_date")

            if RC_PATTERN.search(raw):
                if parsed_mode == PrivacyMode.RELAXED or _valid_rc(raw):
                    cell_detections["RC"] = _new_match("RC", row_idx, col, raw, 0.9, "regex_rc")

            if BANK_ACCOUNT_PATTERN.search(raw) or IBAN_PATTERN.search(raw) or CZ_IBAN_PATTERN.search(raw):
                cell_detections["BANK"] = _new_match("BANK", row_idx, col, raw, 0.9, "regex_bank")

            if is_rc_col and "RC" not in cell_detections:
                cell_detections["RC"] = _new_match("RC", row_idx, col, raw, 0.7, "column_rc_heuristic")

            if is_name_col:
                if parsed_mode == PrivacyMode.STRICT:
                    confidence = 0.72
                elif parsed_mode == PrivacyMode.BALANCED:
                    confidence = 0.62
                else:
                    confidence = 0.55
                cell_detections["NAME"] = _new_match("NAME", row_idx, col, raw, confidence, "column_name_heuristic")

            if is_address_col:
                if parsed_mode == PrivacyMode.STRICT:
                    confidence = 0.72
                elif parsed_mode == PrivacyMode.BALANCED:
                    confidence = 0.62
                else:
                    confidence = 0.55
                cell_detections["ADDRESS"] = _new_match(
                    "ADDRESS",
                    row_idx,
                    col,
                    raw,
                    confidence,
                    "column_address_heuristic",
                )

            if parsed_mode in (PrivacyMode.STRICT, PrivacyMode.BALANCED):
                lowered = raw.lower()
                if POSTCODE_PATTERN.search(raw):
                    cell_detections.setdefault(
                        "ADDRESS",
                        _new_match("ADDRESS", row_idx, col, raw, 0.6, "postcode_heuristic"),
                    )
                if parsed_mode == PrivacyMode.STRICT and any(hint in lowered for hint in ADDRESS_HINTS):
                    cell_detections.setdefault(
                        "ADDRESS",
                        _new_match("ADDRESS", row_idx, col, raw, 0.65, "address_hint_heuristic"),
                    )

            matches.extend(cell_detections.values())

    return _report_from_matches(matches)
