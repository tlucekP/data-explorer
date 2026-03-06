"""Guards for explicit-only AI sending."""

from __future__ import annotations

from typing import Callable


def should_allow_send(
    submit_clicked: bool,
    prompt: str,
    pii_present: bool,
    use_anonymized: bool,
) -> tuple[bool, str]:
    if not submit_clicked:
        return False, "submit_not_clicked"
    if not prompt.strip():
        return False, "empty_prompt"
    if pii_present and not use_anonymized:
        return False, "pii_requires_anonymization"
    return True, "ok"


def dispatch_ai_send(
    submit_clicked: bool,
    prompt: str,
    pii_present: bool,
    use_anonymized: bool,
    sender: Callable[[], str],
) -> tuple[str | None, str]:
    allowed, reason = should_allow_send(
        submit_clicked=submit_clicked,
        prompt=prompt,
        pii_present=pii_present,
        use_anonymized=use_anonymized,
    )
    if not allowed:
        return None, reason
    return sender(), "ok"

