# TS0011: Document Type and ID Inference

> **Status:** Complete
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0011 - Document Type and ID Inference. Covers the `infer_type_and_id()` pure function that determines document type and ID from filename patterns and directory context. Tests are entirely unit-level with parametrised test data covering all inference rules.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0011](../stories/US0011-document-type-and-id-inference.md) | Document Type and ID Inference | Medium |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0011 | AC1 | Infer type from filename prefix | TC0084, TC0085, TC0086, TC0087, TC0088 | Covered |
| US0011 | AC2 | Infer type from singleton filenames | TC0089, TC0090, TC0091 | Covered |
| US0011 | AC3 | Extract document ID from filename | TC0093 | Covered |
| US0011 | AC4 | Singleton document IDs | TC0094 | Covered |
| US0011 | AC5 | Unknown filename defaults to "other" | TC0092 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Pure function with deterministic input/output |
| Integration | No | No database or external service dependencies |
| E2E | No | No frontend or API layer |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest |
| External Services | None |
| Test Data | Filename strings and relative paths |

---

## Test Cases

### TC0084: EP prefix infers type "epic"

**Type:** Unit | **Priority:** Critical | **Story:** US0011 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "EP0001-project-management.md" in path "epics/" | Prefixed filename |
| When | infer_type_and_id("EP0001-project-management.md", "epics/EP0001-project-management.md") | Inference called |
| Then | doc_type is "epic" | Correct type |

**Assertions:**
- [ ] doc_type equals "epic"

---

### TC0085: US prefix infers type "story"

**Type:** Unit | **Priority:** Critical | **Story:** US0011 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "US0045-login-form.md" in path "stories/" | Prefixed filename |
| When | infer_type_and_id("US0045-login-form.md", "stories/US0045-login-form.md") | Inference called |
| Then | doc_type is "story" | Correct type |

**Assertions:**
- [ ] doc_type equals "story"

---

### TC0086: BG prefix infers type "bug"

**Type:** Unit | **Priority:** High | **Story:** US0011 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "BG0003-timeout-error.md" in path "bugs/" | Prefixed filename |
| When | infer_type_and_id("BG0003-timeout-error.md", "bugs/BG0003-timeout-error.md") | Inference called |
| Then | doc_type is "bug" | Correct type |

**Assertions:**
- [ ] doc_type equals "bug"

---

### TC0087: PL prefix infers type "plan"

**Type:** Unit | **Priority:** High | **Story:** US0011 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "PL0001-register-new-project.md" in path "plans/" | Prefixed filename |
| When | infer_type_and_id("PL0001-register-new-project.md", "plans/PL0001-register-new-project.md") | Inference called |
| Then | doc_type is "plan" | Correct type |

**Assertions:**
- [ ] doc_type equals "plan"

---

### TC0088: TS prefix infers type "test-spec"

**Type:** Unit | **Priority:** High | **Story:** US0011 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "TS0001-register-new-project.md" in path "test-specs/" | Prefixed filename |
| When | infer_type_and_id("TS0001-register-new-project.md", "test-specs/TS0001-register-new-project.md") | Inference called |
| Then | doc_type is "test-spec" | Correct type |

**Assertions:**
- [ ] doc_type equals "test-spec"

---

### TC0089: prd.md infers type "prd"

**Type:** Unit | **Priority:** Critical | **Story:** US0011 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "prd.md" in root path | Singleton filename |
| When | infer_type_and_id("prd.md", "prd.md") | Inference called |
| Then | doc_type is "prd" | Correct type |

**Assertions:**
- [ ] doc_type equals "prd"

---

### TC0090: trd.md infers type "trd"

**Type:** Unit | **Priority:** High | **Story:** US0011 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "trd.md" in root path | Singleton filename |
| When | infer_type_and_id("trd.md", "trd.md") | Inference called |
| Then | doc_type is "trd" | Correct type |

**Assertions:**
- [ ] doc_type equals "trd"

---

### TC0091: tsd.md infers type "tsd"

**Type:** Unit | **Priority:** High | **Story:** US0011 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "tsd.md" in root path | Singleton filename |
| When | infer_type_and_id("tsd.md", "tsd.md") | Inference called |
| Then | doc_type is "tsd" | Correct type |

**Assertions:**
- [ ] doc_type equals "tsd"

---

### TC0092: Unknown pattern defaults to type "other"

**Type:** Unit | **Priority:** Critical | **Story:** US0011 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "brand-guide.md" with no known pattern | Unknown filename |
| When | infer_type_and_id("brand-guide.md", "brand-guide.md") | Inference called |
| Then | doc_type is "other" and doc_id is "brand-guide" | Default fallback |

**Assertions:**
- [ ] doc_type equals "other"
- [ ] doc_id equals "brand-guide"

---

### TC0093: Document ID extracted from prefixed filenames

**Type:** Unit | **Priority:** Critical | **Story:** US0011 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Multiple prefixed filenames | Various patterns |
| When | infer_type_and_id is called for each | IDs extracted |
| Then | doc_id matches the prefix + number portion | Correct extraction |

**Assertions:**
- [ ] "EP0001-project-management.md" yields doc_id "EP0001"
- [ ] "US0045-login-form.md" yields doc_id "US0045"
- [ ] "BG0003-timeout-error.md" yields doc_id "BG0003"
- [ ] "PL0001-register-new-project.md" yields doc_id "PL0001"
- [ ] "TS0001-register-new-project.md" yields doc_id "TS0001"

---

### TC0094: Singleton document IDs extracted correctly

**Type:** Unit | **Priority:** High | **Story:** US0011 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Singleton filenames: prd.md, trd.md, tsd.md, personas.md | Known singletons |
| When | infer_type_and_id is called for each | IDs extracted |
| Then | doc_id matches filename stem | Correct extraction |

**Assertions:**
- [ ] "prd.md" yields doc_id "prd"
- [ ] "trd.md" yields doc_id "trd"
- [ ] "tsd.md" yields doc_id "tsd"
- [ ] "personas.md" yields doc_id "personas"

---

### TC0095: _index.md files excluded from import

**Type:** Unit | **Priority:** Critical | **Story:** US0011 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Filename "_index.md" in various directories | Index files |
| When | infer_type_and_id("_index.md", "stories/_index.md") | Inference called |
| Then | Returns SKIP sentinel indicating file should be excluded | Not imported |

**Assertions:**
- [ ] Return value indicates SKIP (None or sentinel)
- [ ] Works for _index.md in any directory (stories/, epics/, plans/)

---

### TC0096: Directory context used as fallback for type inference

**Type:** Unit | **Priority:** Medium | **Story:** US0011 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | File "overview.md" in "epics/" directory (no prefix match) | Directory fallback |
| When | infer_type_and_id("overview.md", "epics/overview.md") | Inference called |
| Then | doc_type is "epic" (from directory), doc_id is "overview" | Directory used |

**Assertions:**
- [ ] doc_type equals "epic" (inferred from epics/ directory)
- [ ] doc_id equals "overview" (filename stem)
- [ ] File in stories/ directory without prefix yields type "story"

---

## Fixtures

```yaml
prefixed_filenames:
  - filename: "EP0001-project-management.md"
    path: "epics/EP0001-project-management.md"
    expected_type: "epic"
    expected_id: "EP0001"
  - filename: "US0045-login-form.md"
    path: "stories/US0045-login-form.md"
    expected_type: "story"
    expected_id: "US0045"
  - filename: "BG0003-timeout-error.md"
    path: "bugs/BG0003-timeout-error.md"
    expected_type: "bug"
    expected_id: "BG0003"
  - filename: "PL0001-register-new-project.md"
    path: "plans/PL0001-register-new-project.md"
    expected_type: "plan"
    expected_id: "PL0001"
  - filename: "TS0001-register-new-project.md"
    path: "test-specs/TS0001-register-new-project.md"
    expected_type: "test-spec"
    expected_id: "TS0001"

singleton_filenames:
  - filename: "prd.md"
    path: "prd.md"
    expected_type: "prd"
    expected_id: "prd"
  - filename: "trd.md"
    path: "trd.md"
    expected_type: "trd"
    expected_id: "trd"
  - filename: "tsd.md"
    path: "tsd.md"
    expected_type: "tsd"
    expected_id: "tsd"

unknown_filename:
  filename: "brand-guide.md"
  path: "brand-guide.md"
  expected_type: "other"
  expected_id: "brand-guide"

index_file:
  filename: "_index.md"
  path: "stories/_index.md"
  expected: SKIP
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0084 | EP prefix infers type "epic" | Pending | - |
| TC0085 | US prefix infers type "story" | Pending | - |
| TC0086 | BG prefix infers type "bug" | Pending | - |
| TC0087 | PL prefix infers type "plan" | Pending | - |
| TC0088 | TS prefix infers type "test-spec" | Pending | - |
| TC0089 | prd.md infers type "prd" | Pending | - |
| TC0090 | trd.md infers type "trd" | Pending | - |
| TC0091 | tsd.md infers type "tsd" | Pending | - |
| TC0092 | Unknown pattern defaults to "other" | Pending | - |
| TC0093 | Document ID extracted from prefixed filenames | Pending | - |
| TC0094 | Singleton document IDs extracted correctly | Pending | - |
| TC0095 | _index.md files excluded from import | Pending | - |
| TC0096 | Directory context used as fallback | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0002](../epics/EP0002-document-sync-and-parsing.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0011 story plan |
