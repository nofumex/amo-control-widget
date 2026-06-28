from __future__ import annotations

from app.core.crypto import SecretBox, mask_secret


def test_crypto_encrypt_decrypt() -> None:
    box = SecretBox("test-secret")
    encrypted = box.encrypt("telegram-token")
    assert encrypted != "telegram-token"
    assert box.decrypt(encrypted) == "telegram-token"


def test_mask_secret() -> None:
    assert mask_secret("123456:ABCDEF") == "123456:A***"
    assert mask_secret("") == ""
