"""Slug generation utility for project names."""

import re
import unicodedata


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a project name.

    Algorithm:
    1. Normalise unicode to NFKD and strip combining marks (accents)
    2. Convert to lowercase
    3. Replace spaces and underscores with hyphens
    4. Remove characters not matching [a-z0-9-]
    5. Collapse consecutive hyphens
    6. Strip leading/trailing hyphens
    """
    # Decompose unicode and remove combining characters (accents)
    normalised = unicodedata.normalize("NFKD", name)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")

    result = ascii_only.lower()
    result = re.sub(r"[\s_]+", "-", result)
    result = re.sub(r"[^a-z0-9-]", "", result)
    result = re.sub(r"-{2,}", "-", result)
    result = result.strip("-")

    return result
