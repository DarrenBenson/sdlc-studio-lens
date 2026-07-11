import type { DocumentListItem } from "../types/index.ts";

export interface TreeNode {
  doc_id: string;
  type: string;
  title: string;
  status: string | null;
  children: TreeNode[];
}

const TYPE_PRIORITY: Record<string, number> = {
  prd: 0,
  trd: 1,
  tsd: 2,
  epic: 3,
  story: 4,
  plan: 5,
  "test-spec": 6,
  bug: 7,
  cr: 8,
  rfc: 9,
  retro: 10,
  review: 11,
  decision: 12,
  pvd: 13,
  persona: 14,
  workflow: 15,
};

// Known artefact id prefixes (mirrors the backend PREFIX_TO_TYPE keys). An id head
// is only recognised for these, so descriptive slugs and bare-number stems are
// ignored rather than mis-read as ids.
const ID_PREFIXES = new Set([
  "EP",
  "US",
  "PL",
  "TS",
  "BG",
  "CR",
  "RFC",
  "WF",
  "RETRO",
  "RV",
]);

// Leading artefact id: a 1-6 letter prefix then either a hyphenated Crockford
// base32 ULID tail (8+ chars, excludes I/L/O/U) or an optional-hyphen 4+ digit
// sequential tail. The ULID branch is tried first so a genuine ULID is never
// truncated. Mirrors backend utils/sdlc_ids._ID_HEAD_RE.
const ID_HEAD_RE =
  /^([A-Za-z]{1,6})(?:-[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{8,}|-?\d{4,})/;

/** The artefact id at the start of a doc_id (prefix + tail), stripping any slug. */
export function idHead(text: string): string | null {
  const match = ID_HEAD_RE.exec(text.trim());
  if (!match) return null;
  if (!ID_PREFIXES.has(match[1].toUpperCase())) return null;
  return match[0];
}

/** Normalise an id for equality: strip non-alphanumerics, upper-case. */
function normId(value: string): string {
  return value.replace(/[^0-9A-Za-z]/g, "").toUpperCase();
}

// Resolve a normalised story/epic reference to its node by comparing normalised
// id heads. This handles both legacy sequential ids ("EP0007", display form
// "EP-0007") and v3 short-ULID ids ("US-01JQK3F8-story" matched by reference
// "US01JQK3F8"), where the previous startsWith match failed on the hyphen.
function findByRef(
  nodes: Map<string, TreeNode>,
  ref: string,
): TreeNode | undefined {
  const target = normId(idHead(ref) ?? ref);
  if (!target) return undefined;
  for (const [docId, node] of nodes) {
    const key = normId(idHead(docId) ?? docId);
    if (key && key === target) return node;
  }
  return undefined;
}

function containsNode(node: TreeNode, target: TreeNode): boolean {
  if (node === target) return true;
  for (const child of node.children) {
    if (containsNode(child, target)) return true;
  }
  return false;
}

function sortNodes(nodes: TreeNode[]): void {
  nodes.sort((a, b) => {
    const ap = TYPE_PRIORITY[a.type] ?? 99;
    const bp = TYPE_PRIORITY[b.type] ?? 99;
    if (ap !== bp) return ap - bp;
    return a.doc_id.localeCompare(b.doc_id);
  });
  for (const node of nodes) {
    sortNodes(node.children);
  }
}

export function buildTree(docs: DocumentListItem[]): TreeNode[] {
  const nodes = new Map<string, TreeNode>();
  for (const doc of docs) {
    nodes.set(doc.doc_id, {
      doc_id: doc.doc_id,
      type: doc.type,
      title: doc.title,
      status: doc.status,
      children: [],
    });
  }

  const placed = new Set<string>();

  for (const doc of docs) {
    let parentNode: TreeNode | undefined;

    if (doc.story) {
      parentNode = findByRef(nodes, doc.story);
    } else if (doc.epic && doc.type !== "epic") {
      parentNode = findByRef(nodes, doc.epic);
    }

    if (parentNode && parentNode.doc_id !== doc.doc_id) {
      const childNode = nodes.get(doc.doc_id)!;
      // Skip an edge that would make the node an ancestor of itself: if the
      // resolved parent already sits within the child's subtree, attaching
      // the child here would form a cycle and make sortNodes recurse forever.
      if (!containsNode(childNode, parentNode)) {
        parentNode.children.push(childNode);
        placed.add(doc.doc_id);
      }
    }
  }

  const roots: TreeNode[] = [];
  for (const doc of docs) {
    if (!placed.has(doc.doc_id)) {
      roots.push(nodes.get(doc.doc_id)!);
    }
  }

  sortNodes(roots);
  return roots;
}
