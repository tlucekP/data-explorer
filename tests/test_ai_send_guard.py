from __future__ import annotations

from llm.send_guard import dispatch_ai_send


def test_no_click_never_calls_sender() -> None:
    called = {"count": 0}

    def sender() -> str:
        called["count"] += 1
        return "ok"

    response, reason = dispatch_ai_send(
        submit_clicked=False,
        prompt="Ahoj",
        pii_present=False,
        use_anonymized=False,
        sender=sender,
    )

    assert response is None
    assert reason == "submit_not_clicked"
    assert called["count"] == 0


def test_blocks_when_pii_and_not_anonymized() -> None:
    called = {"count": 0}

    def sender() -> str:
        called["count"] += 1
        return "ok"

    response, reason = dispatch_ai_send(
        submit_clicked=True,
        prompt="Ahoj",
        pii_present=True,
        use_anonymized=False,
        sender=sender,
    )

    assert response is None
    assert reason == "pii_requires_anonymization"
    assert called["count"] == 0
