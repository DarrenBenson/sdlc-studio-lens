/**
 * A rehype transform that turns inline artefact id references in the rendered
 * markdown body (e.g. `US0001`, `CR-01KX8B82`, `[[CR-0496]]`) into internal
 * links to the referenced document.
 *
 * References are only linkified when they resolve against a supplied map, so
 * dangling references stay as plain text rather than becoming broken links.
 * Id recognition reuses the same `idHead` / `normId` logic as the tree builder.
 */

import { idHead, normId } from "./buildTree.ts";

/** Minimal hast node shape (avoids a dependency on @types/hast). */
interface HastNode {
  type: string;
  tagName?: string;
  value?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
}

/** A resolved document target for an id reference. */
export interface IdTarget {
  type: string;
  doc_id: string;
}

export interface IdLinkOptions {
  /** Resolve a raw reference to its document, or undefined if unknown. */
  resolve: (ref: string) => IdTarget | undefined;
  /** Build the route href for a resolved target. */
  href: (target: IdTarget) => string;
}

// Do not linkify inside these elements (code samples, existing links, headings).
const SKIP_TAGS = new Set([
  "a",
  "code",
  "pre",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
]);

// Wiki-form `[[ID]]` or a bare id with a ULID or 4+ digit tail, bounded so it is
// not matched inside a longer alphanumeric token. Mirrors ID_HEAD_RE's tail.
const REF_RE =
  /\[\[\s*([A-Za-z]{1,6}(?:-[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{8,}|-?\d{4,}))\s*\]\]|(?<![A-Za-z0-9])([A-Za-z]{1,6}(?:-[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{8,}|-?\d{4,}))(?![A-Za-z0-9])/g;

function linkifyText(value: string, options: IdLinkOptions): HastNode[] {
  REF_RE.lastIndex = 0;
  const out: HastNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = REF_RE.exec(value)) !== null) {
    const ref = match[1] ?? match[2];
    const head = idHead(ref);
    if (!head) continue;
    const target = options.resolve(head);
    if (!target) continue; // unknown reference: leave the raw text in place

    if (match.index > last) {
      out.push({ type: "text", value: value.slice(last, match.index) });
    }
    out.push({
      type: "element",
      tagName: "a",
      properties: {
        href: options.href(target),
        className: ["id-ref"],
        "data-id-ref": "true",
      },
      children: [{ type: "text", value: head }],
    });
    last = match.index + match[0].length;
  }

  if (out.length === 0) return [{ type: "text", value }];
  if (last < value.length) {
    out.push({ type: "text", value: value.slice(last) });
  }
  return out;
}

function walk(node: HastNode, skip: boolean, options: IdLinkOptions): void {
  if (!node.children) return;
  const next: HastNode[] = [];
  for (const child of node.children) {
    if (child.type === "text" && !skip && child.value) {
      next.push(...linkifyText(child.value, options));
    } else {
      const childSkip =
        skip || (child.tagName ? SKIP_TAGS.has(child.tagName) : false);
      walk(child, childSkip, options);
      next.push(child);
    }
  }
  node.children = next;
}

/** rehype plugin factory: `[rehypeIdLinks, options]`. */
export function rehypeIdLinks(options: IdLinkOptions) {
  return (tree: HastNode): void => {
    walk(tree, false, options);
  };
}

/**
 * Build a normalised-id lookup from a document list. Keys are the normalised
 * id head so `US0001`, `US-0001` and `[[US0001]]` all resolve to one entry.
 */
export function buildRefMap(
  docs: { doc_id: string; type: string }[],
): Map<string, IdTarget> {
  const map = new Map<string, IdTarget>();
  for (const doc of docs) {
    const key = normId(idHead(doc.doc_id) ?? doc.doc_id);
    if (key && !map.has(key)) {
      map.set(key, { type: doc.type, doc_id: doc.doc_id });
    }
  }
  return map;
}

/** Resolve a raw reference against a ref map via its normalised id head. */
export function resolveRef(
  map: Map<string, IdTarget>,
  ref: string,
): IdTarget | undefined {
  const key = normId(idHead(ref) ?? ref);
  return key ? map.get(key) : undefined;
}
