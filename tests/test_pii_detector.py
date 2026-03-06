from __future__ import annotations

from datetime import date

import pandas as pd

from privacy.pii_detector import PrivacyMode, detect_csv_pii, detect_text_pii


def test_detect_csv_pii_core_types() -> None:
    df = pd.DataFrame(
        {
            "email": ["jan.novak@example.com", "x"],
            "telefon": ["+420 777 888 999", ""],
            "rodne_cislo": ["850101/1234", ""],
            "iban": ["CZ6508000000192000145399", ""],
        }
    )
    report = detect_csv_pii(df, mode=PrivacyMode.STRICT)

    assert report.has_pii is True
    assert report.totals_by_type.get("EMAIL", 0) >= 1
    assert report.totals_by_type.get("PHONE", 0) >= 1
    assert report.totals_by_type.get("RC", 0) >= 1
    assert report.totals_by_type.get("BANK", 0) >= 1


def test_detect_text_date_and_email() -> None:
    text = "Kontakt: jana@firma.cz\nDatum narozeni: 1988-05-17"
    report = detect_text_pii(text, mode=PrivacyMode.BALANCED)

    assert report.has_pii is True
    assert report.totals_by_type.get("EMAIL", 0) == 1
    assert report.totals_by_type.get("DOB", 0) == 1


def test_detect_csv_dob_requires_hint_or_old_year_and_excludes_timestamps() -> None:
    current_year = date.today().year
    old_year = current_year - 20
    recent_year = current_year - 2

    df = pd.DataFrame(
        {
            "created_at": [f"{old_year}-01-01", f"{old_year}-01-02"],
            "updated_at": [f"{old_year}-02-01", f"{old_year}-02-02"],
            "timestamp": [f"{old_year}-03-01", f"{old_year}-03-02"],
            "created": [f"{old_year}-04-01", f"{old_year}-04-02"],
            "modified": [f"{old_year}-05-01", f"{old_year}-05-02"],
            "event_date": [f"{old_year}-06-01", f"{recent_year}-06-01"],
            "date_of_birth": [f"{recent_year}-07-01", f"{recent_year}-07-02"],
            "birth": [f"{recent_year}-08-01", f"{recent_year}-08-02"],
            "narozeni": [f"{recent_year}-09-01", f"{recent_year}-09-02"],
        }
    )

    report = detect_csv_pii(df, mode=PrivacyMode.STRICT)

    # DOB should be detected only via old-year rule or explicit DOB-like column hint.
    assert report.totals_by_type.get("DOB", 0) == 7

    timestamp_columns = {"created_at", "updated_at", "timestamp", "created", "modified"}
    assert not any(match.pii_type == "DOB" and match.column in timestamp_columns for match in report.matches)

    # event_date should include only the old date row.
    event_date_rows = [m.row_idx for m in report.matches if m.pii_type == "DOB" and m.column == "event_date"]
    assert event_date_rows == [0]


def test_detect_text_recent_date_is_not_dob() -> None:
    current_year = date.today().year
    text = f"Vytvoreno: {current_year - 1}-05-12"
    report = detect_text_pii(text, mode=PrivacyMode.BALANCED)
    assert report.totals_by_type.get("DOB", 0) == 0
