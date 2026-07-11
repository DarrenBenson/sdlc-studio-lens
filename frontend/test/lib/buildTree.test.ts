/**
 * buildTree tests.
 * Regression cover for CR-01KX8B1W: self-referential and cyclic
 * story/epic frontmatter must not recurse infinitely (RangeError).
 */
import { describe, expect, it } from "vitest";
import { buildTree, type TreeNode } from "../../src/lib/buildTree";
import type { DocumentListItem } from "../../src/types/index.ts";

function makeDoc(
  overrides: Partial<DocumentListItem> & Pick<DocumentListItem, "doc_id" | "type">,
): DocumentListItem {
  return {
    title: overrides.doc_id,
    status: null,
    owner: null,
    priority: null,
    story_points: null,
    epic: null,
    story: null,
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function collectIds(nodes: TreeNode[]): string[] {
  const ids: string[] = [];
  for (const node of nodes) {
    ids.push(node.doc_id);
    ids.push(...collectIds(node.children));
  }
  return ids;
}

describe("buildTree", () => {
  // A document whose own doc_id starts with its story prefix must not
  // become its own child (which previously blew the stack in sortNodes).
  it("does not attach a self-referential node as its own child", () => {
    const docs: DocumentListItem[] = [
      makeDoc({ doc_id: "US0001-x", type: "story", story: "US0001" }),
    ];

    let tree: TreeNode[] = [];
    expect(() => {
      tree = buildTree(docs);
    }).not.toThrow();

    const ids = collectIds(tree);
    expect(ids).toEqual(["US0001-x"]);
    expect(tree[0].children).toEqual([]);
  });

  // A two-node cycle (A references B, B references A) must resolve to a
  // finite forest rather than recursing infinitely.
  it("does not recurse infinitely on a two-node cycle", () => {
    const docs: DocumentListItem[] = [
      makeDoc({ doc_id: "US0001", type: "story", story: "US0002" }),
      makeDoc({ doc_id: "US0002", type: "story", story: "US0001" }),
    ];

    let tree: TreeNode[] = [];
    expect(() => {
      tree = buildTree(docs);
    }).not.toThrow();

    const ids = collectIds(tree);
    expect(ids).toHaveLength(2);
    expect(ids.sort()).toEqual(["US0001", "US0002"]);
  });

  // Regression: a normal epic -> story -> plan hierarchy still nests.
  it("nests a normal epic -> story -> plan hierarchy", () => {
    const docs: DocumentListItem[] = [
      makeDoc({ doc_id: "EP0001", type: "epic" }),
      makeDoc({ doc_id: "US0001", type: "story", epic: "EP0001" }),
      makeDoc({ doc_id: "PL0001", type: "plan", story: "US0001" }),
    ];

    const tree = buildTree(docs);

    expect(tree).toHaveLength(1);
    const epic = tree[0];
    expect(epic.doc_id).toBe("EP0001");
    expect(epic.children).toHaveLength(1);

    const story = epic.children[0];
    expect(story.doc_id).toBe("US0001");
    expect(story.children).toHaveLength(1);

    const plan = story.children[0];
    expect(plan.doc_id).toBe("PL0001");
    expect(plan.children).toEqual([]);

    expect(collectIds(tree).sort()).toEqual(["EP0001", "PL0001", "US0001"]);
  });

  // CR-01KX8YD6: v3 short-ULID ids. The story's normalised epic reference
  // "EP01KX8A00" must resolve against the epic node keyed by the full doc_id
  // stem "EP-01KX8A00-core". The legacy startsWith match fails here because
  // "EP-01KX8A00-core".startsWith("EP01KX8A00") is false (the hyphen differs).
  it("nests a ULID story under its ULID epic via normalised ids", () => {
    const docs: DocumentListItem[] = [
      makeDoc({ doc_id: "EP-01KX8A00-core", type: "epic" }),
      makeDoc({
        doc_id: "US-01KX8B90-x",
        type: "story",
        epic: "EP01KX8A00",
      }),
    ];

    const tree = buildTree(docs);

    expect(tree).toHaveLength(1);
    const epic = tree[0];
    expect(epic.doc_id).toBe("EP-01KX8A00-core");
    expect(epic.children).toHaveLength(1);
    expect(epic.children[0].doc_id).toBe("US-01KX8B90-x");
    expect(collectIds(tree).sort()).toEqual([
      "EP-01KX8A00-core",
      "US-01KX8B90-x",
    ]);
  });

  // CR-01KX8YD6: a hyphenated display-form reference ("US-01KX8B90") resolves to
  // the node keyed by "US-01KX8B90-x" once both sides are normalised.
  it("resolves a hyphenated ULID reference to its node", () => {
    const docs: DocumentListItem[] = [
      makeDoc({ doc_id: "US-01KX8B90-x", type: "story" }),
      makeDoc({
        doc_id: "PL-01KX8C10-y",
        type: "plan",
        story: "US-01KX8B90",
      }),
    ];

    const tree = buildTree(docs);

    expect(tree).toHaveLength(1);
    const story = tree[0];
    expect(story.doc_id).toBe("US-01KX8B90-x");
    expect(story.children).toHaveLength(1);
    expect(story.children[0].doc_id).toBe("PL-01KX8C10-y");
  });

  // CR-01KX8YD6: legacy hyphenated display form ("CR-0003" file "CR0003").
  it("resolves a legacy hyphenated sequential reference", () => {
    const docs: DocumentListItem[] = [
      makeDoc({ doc_id: "EP0007", type: "epic" }),
      makeDoc({ doc_id: "US0042", type: "story", epic: "EP-0007" }),
    ];

    const tree = buildTree(docs);

    expect(tree).toHaveLength(1);
    expect(tree[0].doc_id).toBe("EP0007");
    expect(tree[0].children[0].doc_id).toBe("US0042");
  });
});
