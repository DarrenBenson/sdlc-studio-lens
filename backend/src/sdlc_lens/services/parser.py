"""Blockquote frontmatter parser for sdlc-studio markdown documents."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Regex: matches "> **Key:** Value" - the colon may be inside or outside bold
_KV_PATTERN = re.compile(r"^>\s+\*\*(.+?)\*\*:?\s*(.*?)\s*$")

# Regex: matches "**Key:** Value" without blockquote prefix
_PLAIN_KV_PATTERN = re.compile(r"^\*\*(.+?)\*\*:?\s*(.*?)\s*$")


def _normalise_key(key: str) -> str:
    """Convert Title Case key to snake_case.

    Strips trailing colons (from ``**Key:**`` format) before converting.
    """
    cleaned = key.strip().rstrip(":")
    return re.sub(r"\s+", "_", cleaned).lower()


def _is_kv_line(line: str) -> bool:
    """Check if a line matches the key-value pattern."""
    return _KV_PATTERN.match(line) is not None


@dataclass
class ParseResult:
    """Result of parsing an sdlc-studio markdown document."""

    title: str | None = None
    metadata: dict[str, str | int | None] = field(default_factory=dict)
    body: str = ""


def parse_document(content: str) -> ParseResult:
    """Parse sdlc-studio markdown document.

    Extracts blockquote frontmatter (``> **Key:** Value``), the first
    ``#`` heading as title, and the remaining body content.

    Args:
        content: Raw markdown text.

    Returns:
        ParseResult with title, metadata dict, and body content.
    """
    # Normalise line endings
    content = content.replace("\r\n", "\n")

    lines = content.split("\n")
    metadata: dict[str, str | int | None] = {}
    title: str | None = None

    # Find the first contiguous blockquote block (the frontmatter).
    # Documents may start with a heading before the blockquote, e.g.:
    #   # Title
    #   > **Status:** Done
    # So we scan forward past non-blockquote lines to find the first
    # contiguous run of `>` lines.
    fm_start: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(">") and not stripped.startswith(">>"):
            fm_start = i
            break

    fm_lines: list[str] = []
    frontmatter_end = 0
    if fm_start is not None:
        for i in range(fm_start, len(lines)):
            stripped = lines[i].strip()
            if not stripped.startswith(">") or stripped.startswith(">>"):
                frontmatter_end = i
                break
            fm_lines.append(lines[i])
        else:
            # All remaining lines from fm_start were blockquote
            if fm_lines:
                frontmatter_end = len(lines)

    # Phase 2: parse collected frontmatter lines
    # Pre-compute which non-KV lines are continuation vs malformed.
    # A single non-KV line followed by a KV line is malformed (skip).
    # A run of 2+ non-KV lines is continuation of the preceding key.
    is_continuation: set[int] = set()
    i = 0
    while i < len(fm_lines):
        if not _is_kv_line(fm_lines[i]):
            # Count consecutive non-KV lines from position i
            run_start = i
            while i < len(fm_lines) and not _is_kv_line(fm_lines[i]):
                i += 1
            run_length = i - run_start
            # Single non-KV line before a KV line is malformed
            # Multiple non-KV lines (or non-KV at end of block) are continuation
            if run_length > 1 or i >= len(fm_lines):
                for j in range(run_start, run_start + run_length):
                    is_continuation.add(j)
        else:
            i += 1

    current_key: str | None = None
    for idx, line in enumerate(fm_lines):
        match = _KV_PATTERN.match(line)
        if match:
            raw_key = match.group(1)
            raw_value = match.group(2).strip()
            key = _normalise_key(raw_key)
            current_key = key
            metadata[key] = raw_value
        elif current_key is not None and idx in is_continuation:
            continuation = re.sub(r"^>\s?", "", line).strip()
            if continuation:
                existing = metadata[current_key]
                if isinstance(existing, str) and existing:
                    metadata[current_key] = f"{existing} {continuation}"
                else:
                    metadata[current_key] = continuation

    # Fallback: if no blockquote frontmatter found, try plain bold key-value
    # lines (e.g. "**Status:** Done" without ">" prefix).  Scan from the
    # start of the document, stopping at the first non-matching, non-blank,
    # non-heading line.
    if not metadata:
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            plain_match = _PLAIN_KV_PATTERN.match(stripped)
            if plain_match:
                key = _normalise_key(plain_match.group(1))
                metadata[key] = plain_match.group(2).strip()
            elif stripped == "---":
                continue
            else:
                break

    # Convert story_points to int if present
    if "story_points" in metadata:
        raw = metadata["story_points"]
        if isinstance(raw, str):
            try:
                metadata["story_points"] = int(raw)
            except (ValueError, TypeError):
                metadata["story_points"] = None

    # Extract title from first # heading (anywhere in document)
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Body: everything after frontmatter block
    body_lines = lines[frontmatter_end:]
    body = "\n".join(body_lines)

    return ParseResult(title=title, metadata=metadata, body=body)
