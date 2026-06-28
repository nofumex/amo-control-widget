from __future__ import annotations

import hashlib
import hmac
import time


def sign_value(value: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def verify_signed_value(token: str, secret: str) -> str:
    value, separator, signature = token.rpartition(".")
    if not separator:
        raise ValueError("Malformed token")
    expected = hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid token signature")
    return value


def issue_tenant_token(tenant_id: int, secret: str, ttl_seconds: int = 86400) -> str:
    expires_at = int(time.time()) + ttl_seconds
    return sign_value(f"{tenant_id}:{expires_at}", secret)


def verify_tenant_token(token: str, secret: str) -> int:
    value = verify_signed_value(token, secret)
    tenant_id_text, expires_text = value.split(":", 1)
    if int(expires_text) < int(time.time()):
        raise ValueError("Token expired")
    return int(tenant_id_text)
