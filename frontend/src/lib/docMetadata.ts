/**
 * Parse the leading `> **Field:** value` blockquote block that heads most
 * artefacts into structured metadata, returning the remaining markdown body.
 *
 * The block is only recognised when it sits at the very top of the document
 * (optionally after a single leading heading) AND every non-blank line matches
 * the `**Label:** value` shape. A genuine prose blockquote is therefore left
 * untouched in the body.
 */

/** A single parsed metadata field from the header blockquote. */
export interface DocMetaField {
  /** Stable key for React lists (slugified label). */
  key: string;
  /** Human label exactly as authored, e.g. "Raised by". */
  label: string;
  /** Field value (may be empty). */
  value: string;
}

/** Result of splitting a document into its header metadata and body. */
export interface ParsedDocContent {
  fields: DocMetaField[];
  body: string;
}

const HEADING_RE = /^#{1,6}\s/;
const QUOTE_RE = /^\s*>/;
// `**Label:** value` (colon inside the bold) or `**Label**: value`.
const FIELD_COLON_INSIDE_RE = /^\*\*(.+?):\*\*\s*(.*)$/;
const FIELD_COLON_OUTSIDE_RE = /^\*\*(.+?)\*\*:\s*(.*)$/;

function slugKey(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function extractMetadataHeader(content: string): ParsedDocContent {
  const lines = content.split("\n");
  let idx = 0;

  // Skip leading blank lines.
  while (idx < lines.length && lines[idx].trim() === "") idx++;

  // Allow a single leading ATX heading (the artefact title) before the block.
  if (idx < lines.length && HEADING_RE.test(lines[idx])) {
    idx++;
    while (idx < lines.length && lines[idx].trim() === "") idx++;
  }

  // Collect the contiguous blockquote block.
  const blockStart = idx;
  while (idx < lines.length && QUOTE_RE.test(lines[idx])) idx++;
  const quoteLines = lines.slice(blockStart, idx);
  if (quoteLines.length === 0) {
    return { fields: [], body: content };
  }

  const fields: DocMetaField[] = [];
  for (const raw of quoteLines) {
    const stripped = raw.replace(/^\s*>\s?/, "");
    if (stripped.trim() === "") continue; // blank line within the blockquote
    const match =
      FIELD_COLON_INSIDE_RE.exec(stripped) ??
      FIELD_COLON_OUTSIDE_RE.exec(stripped);
    if (!match) {
      // A non-field line means this is a real prose blockquote: leave it be.
      return { fields: [], body: content };
    }
    const label = match[1].trim();
    fields.push({ key: slugKey(label) || label, label, value: match[2].trim() });
  }

  if (fields.length === 0) {
    return { fields: [], body: content };
  }

  const body = [...lines.slice(0, blockStart), ...lines.slice(idx)]
    .join("\n")
    .replace(/^\n+/, "")
    .replace(/\n{3,}/g, "\n\n");

  return { fields, body };
}
