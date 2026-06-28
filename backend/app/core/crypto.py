from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class SecretBox:
    def __init__(self, key_or_secret: str) -> None:
        raw = key_or_secret.strip()
        if not raw:
            raise ValueError("FERNET_KEY or APP_SECRET_KEY must be configured")
        try:
            self._fernet = Fernet(raw.encode("utf-8"))
        except ValueError:
            self._fernet = Fernet(derive_fernet_key(raw))

    def encrypt(self, value: str | None) -> str:
        if value is None:
            return ""
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str | None) -> str:
        if not token:
            return ""
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Cannot decrypt stored secret") from exc


def mask_secret(value: str | None, visible_prefix: int = 8) -> str:
    if not value:
        return ""
    if len(value) <= visible_prefix:
        return "***"
    return f"{value[:visible_prefix]}***"
