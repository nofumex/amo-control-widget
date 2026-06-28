from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode


@dataclass(frozen=True)
class SignedRequest:
    method: str
    path: str
    query: str
    timestamp: int
    account_id: int
    body: bytes = b""


@dataclass(frozen=True)
class WidgetPrincipal:
    account_id: int
    subdomain: str = ""


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


def canonical_query(raw_query: str) -> str:
    pairs = parse_qsl(raw_query, keep_blank_values=True)
    return urlencode(sorted(pairs), doseq=True)


def body_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical_widget_message(request: SignedRequest) -> str:
    return "\n".join(
        [
            request.method.upper(),
            request.path,
            canonical_query(request.query),
            str(request.timestamp),
            str(request.account_id),
            body_sha256(request.body),
        ]
    )


def compute_request_signature(request: SignedRequest, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), canonical_widget_message(request).encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_request_signature(
    request: SignedRequest,
    signature: str,
    secret: str,
    *,
    ttl_seconds: int,
    now: int | None = None,
) -> bool:
    if not secret:
        return False
    current = int(time.time()) if now is None else now
    if abs(current - request.timestamp) > ttl_seconds:
        return False
    expected = compute_request_signature(request, secret)
    return hmac.compare_digest(expected, signature.strip())


def webhook_dedup_key(source: str, body: bytes) -> str:
    return f"{source}:{hashlib.sha256(body).hexdigest()}"
