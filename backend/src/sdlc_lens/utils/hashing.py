"""SHA-256 hash computation for file content."""

import hashlib


def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hex digest of content bytes."""
    return hashlib.sha256(content).hexdigest()
