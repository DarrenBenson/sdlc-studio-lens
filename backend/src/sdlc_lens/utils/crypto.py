"""Symmetric encryption for secrets stored at rest (e.g. GitHub PATs).

Encryption is opt-in and config-gated. When ``settings.token_encryption_key``
is set to a urlsafe base64 Fernet key, ``encrypt_token`` returns Fernet
ciphertext carrying a distinguishable ``enc:v1:`` prefix and ``decrypt_token``
reverses it. Values without the prefix are treated as legacy plaintext and
returned unchanged, so tokens written before encryption was enabled keep
working. When no key is configured, both helpers are pass-through and the
database stays plaintext (behaviour unchanged).
"""

from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken

from sdlc_lens.config import settings

logger = logging.getLogger(__name__)

# Marks a stored value as ciphertext produced by this module. The version
# segment leaves room to rotate the scheme later without ambiguity.
ENC_PREFIX = "enc:v1:"


def _fernet() -> Fernet | None:
    """Build a Fernet instance from the configured key, or None if unset."""
    key = settings.token_encryption_key
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext: str | None) -> str | None:
    """Encrypt a token for storage.

    Returns Fernet ciphertext with the ``enc:v1:`` prefix when a key is
    configured. When no key is configured, returns the plaintext unchanged
    (opt-in encryption). ``None`` passes through as ``None``.
    """
    if plaintext is None:
        return None
    fernet = _fernet()
    if fernet is None:
        return plaintext
    token = fernet.encrypt(plaintext.encode()).decode()
    return f"{ENC_PREFIX}{token}"


def decrypt_token(stored: str | None) -> str | None:
    """Decrypt a stored token back to its plaintext.

    Values carrying the ``enc:v1:`` prefix are decrypted with the configured
    key. Non-prefixed values are legacy plaintext and returned unchanged, even
    when a key is configured. ``None`` passes through as ``None``.

    When the configured key cannot open a prefixed value (the key was rotated
    or replaced, or the ciphertext is corrupted), decryption fails gracefully:
    a warning is logged and ``None`` is returned (treated as "no usable token")
    rather than raising, so one bad row cannot 500 the whole project list.
    """
    if stored is None:
        return None
    if not stored.startswith(ENC_PREFIX):
        # Legacy plaintext (stored before encryption was enabled).
        return stored
    fernet = _fernet()
    if fernet is None:
        # Prefixed but no key available: cannot decrypt, return as-is.
        return stored
    ciphertext = stored[len(ENC_PREFIX) :]
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Wrong key (rotated/replaced) or corrupted ciphertext. Do not leak the
        # stored value; treat as no usable token so callers degrade gracefully.
        logger.warning("Stored token could not be decrypted with the configured key")
        return None
