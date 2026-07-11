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
};

function findByPrefix(
  nodes: Map<string, TreeNode>,
  prefix: string,
): TreeNode | undefined {
  for (const [docId, node] of nodes) {
    if (docId.startsWith(prefix)) return node;
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
      parentNode = findByPrefix(nodes, doc.story);
    } else if (doc.epic && doc.type !== "epic") {
      parentNode = findByPrefix(nodes, doc.epic);
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
