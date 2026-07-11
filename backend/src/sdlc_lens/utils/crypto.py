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

from cryptography.fernet import Fernet

from sdlc_lens.config import settings

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
    return fernet.decrypt(ciphertext.encode()).decode()
