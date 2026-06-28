from __future__ import annotations

import time

from app.core.security import SignedRequest, compute_request_signature, webhook_dedup_key


def test_webhook_signature_adapter_and_dedup_key() -> None:
    body = b'{"account":{"id":123}}'
    request = SignedRequest("POST", "/api/webhooks/amo", "", int(time.time()), 0, body)
    signature = compute_request_signature(request, "webhook-secret")
    assert signature
    assert webhook_dedup_key("amo", body) == webhook_dedup_key("amo", body)
    assert webhook_dedup_key("amo", body) != webhook_dedup_key("digital_pipeline", body)
