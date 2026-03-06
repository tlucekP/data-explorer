from __future__ import annotations

import pandas as pd

from privacy.anonymizer import anonymize_csv
from privacy.pii_detector import PrivacyMode, detect_csv_pii


def test_anonymizer_keeps_consistent_tokens() -> None:
    df = pd.DataFrame(
        {
            "email": ["jan.novak@example.com", "jan.novak@example.com", "eva@test.cz"],
            "telefon": ["+420 777 888 999", "+420 777 888 999", "+420 123 456 789"],
        }
    )
    report = detect_csv_pii(df, mode=PrivacyMode.STRICT)
    result = anonymize_csv(df, report)

    assert result.anonymized_df is not None
    assert result.anonymized_df.loc[0, "email"] == result.anonymized_df.loc[1, "email"]
    assert str(result.anonymized_df.loc[0, "email"]).startswith("EMAIL_")
    assert str(result.anonymized_df.loc[0, "telefon"]).startswith("PHONE_")
    assert result.replaced_counts.get("EMAIL", 0) >= 3
    assert result.replaced_counts.get("PHONE", 0) >= 3
