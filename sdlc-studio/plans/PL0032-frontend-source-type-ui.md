# PL0032: Frontend Source Type UI - Implementation Plan

> **Status:** Done
> **Story:** [US0032: Frontend Source Type UI](../stories/US0032-frontend-source-type-ui.md)
> **Epic:** [EP0007: GitHub Repository Sync](../epics/EP0007-github-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Language:** TypeScript / React

## Overview

Update the frontend to support registering and managing GitHub-sourced projects alongside the existing local filesystem projects. The `ProjectForm` component gains a source type toggle (Local / GitHub) that conditionally shows the appropriate fields: SDLC Path for local, or Repository URL, Branch, Subdirectory Path, and Access Token for GitHub. The `ProjectCard` component displays a small source badge ("Local" or "GitHub") and shows the repository URL instead of the filesystem path for GitHub projects. TypeScript interfaces are updated to include the new source fields.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Source toggle | ProjectForm has a Local / GitHub toggle that switches visible fields |
| AC2 | Local fields | "Local" shows SDLC Path field (existing behaviour) |
| AC3 | GitHub fields | "GitHub" shows Repository URL (required), Branch (default "main"), Subdirectory (default "sdlc-studio"), Access Token (password field, optional) |
| AC4 | Form submission | Submitting sends correct `source_type` and relevant fields to API |
| AC5 | Source badge | ProjectCard shows "Local" or "GitHub" badge |
| AC6 | Edit mode | Editing a GitHub project pre-populates the GitHub fields |
| AC7 | Type definitions | TypeScript interfaces updated with source fields |

---

## Technical Context

### Language & Framework
- **UI:** React 19.2 with TypeScript
- **Build:** Vite 7
- **Styling:** Tailwind CSS 4.1
- **Testing:** Vitest + React Testing Library v16

### Existing Patterns

**ProjectForm** (`frontend/src/components/ProjectForm.tsx`):
- Takes `mode`, `initialName`, `initialPath`, `onSubmit`, `onCancel`, `error` props
- Manages `name` and `sdlcPath` state
- Submits `ProjectCreate` or `ProjectUpdate` via `onSubmit` callback

**ProjectCard** (`frontend/src/components/ProjectCard.tsx`):
- Displays project name, `sdlc_path`, sync status badge, document count, and action buttons
- Uses `STATUS_COLOURS` and `STATUS_LABELS` maps for sync status styling

**Types** (`frontend/src/types/index.ts`):
- `Project` interface with `slug`, `name`, `sdlc_path`, `sync_status`, etc.
- `ProjectCreate` with `name` and `sdlc_path`
- `ProjectUpdate` with optional `name` and `sdlc_path`

**Settings page** (`frontend/src/pages/Settings.tsx`):
- Renders `ProjectForm` for add and edit modes
- Passes `initialName` and `initialPath` when editing

### Dependencies
- **PL0031:** API returns `source_type`, `repo_url`, `repo_branch`, `repo_path`, `masked_token` in project responses

---

## Recommended Approach

**Strategy:** TDD (Component)
**Rationale:** Form behaviour (toggle, conditional fields, submission data) is testable with React Testing Library. Component tests verify the toggle switches fields, required validation works, and submitted data includes the correct source-specific fields.

### Test Priority
1. Source type toggle renders and switches fields
2. Local mode shows SDLC Path, hides GitHub fields
3. GitHub mode shows repo fields, hides SDLC Path
4. Form submission includes correct source_type and fields
5. Edit mode pre-populates GitHub fields
6. ProjectCard shows source badge
7. TypeScript compilation passes

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Update TypeScript interfaces | `frontend/src/types/index.ts` | PL0031 | [ ] |
| 2 | Add source toggle to ProjectForm | `frontend/src/components/ProjectForm.tsx` | 1 | [ ] |
| 3 | Add source badge to ProjectCard | `frontend/src/components/ProjectCard.tsx` | 1 | [ ] |
| 4 | Update Settings page | `frontend/src/pages/Settings.tsx` | 2 | [ ] |
| 5 | Write ProjectForm tests | `frontend/test/components/ProjectForm.test.tsx` | 2 | [ ] |
| 6 | Write ProjectCard tests | `frontend/test/components/ProjectCard.test.tsx` | 3 | [ ] |
| 7 | Verify TypeScript compilation | manual | 1 | [ ] |

---

## Implementation Phases

### Phase 1: Type Definitions

**Goal:** Update TypeScript interfaces to match the new API schema.

- [ ] Update `frontend/src/types/index.ts`:

```typescript
/** Project as returned by GET /api/v1/projects. */
export interface Project {
  slug: string;
  name: string;
  sdlc_path: string | null;
  source_type: "local" | "github";
  repo_url: string | null;
  repo_branch: string;
  repo_path: string;
  masked_token: string | null;
  sync_status: SyncStatus;
  sync_error: string | null;
  last_synced_at: string | null;
  document_count: number;
  created_at: string;
}

/** Request body for POST /api/v1/projects. */
export interface ProjectCreate {
  name: string;
  source_type: "local" | "github";
  sdlc_path?: string;
  repo_url?: string;
  repo_branch?: string;
  repo_path?: string;
  access_token?: string;
}

/** Request body for PUT /api/v1/projects/{slug}. */
export interface ProjectUpdate {
  name?: string;
  sdlc_path?: string;
  repo_url?: string;
  repo_branch?: string;
  repo_path?: string;
  access_token?: string;
}
```

**Key changes:**
- `sdlc_path` becomes `string | null` (was `string`)
- New fields: `source_type`, `repo_url`, `repo_branch`, `repo_path`, `masked_token`
- `ProjectCreate` gains `source_type` (required) and optional repo fields
- `ProjectUpdate` gains optional repo fields

**Files:**
- `frontend/src/types/index.ts`

### Phase 2: ProjectForm Updates

**Goal:** Add source type toggle with conditional field rendering.

- [ ] Update `frontend/src/components/ProjectForm.tsx`:

```typescript
interface ProjectFormProps {
  mode: "add" | "edit";
  initialName?: string;
  initialPath?: string;
  initialSourceType?: "local" | "github";
  initialRepoUrl?: string;
  initialRepoBranch?: string;
  initialRepoPath?: string;
  onSubmit: (data: ProjectCreate | ProjectUpdate) => Promise<void>;
  onCancel?: () => void;
  error: string | null;
}
```

**Component structure:**

```tsx
export function ProjectForm({
  mode,
  initialName = "",
  initialPath = "",
  initialSourceType = "local",
  initialRepoUrl = "",
  initialRepoBranch = "main",
  initialRepoPath = "sdlc-studio",
  onSubmit,
  onCancel,
  error,
}: ProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [sourceType, setSourceType] = useState<"local" | "github">(initialSourceType);
  const [sdlcPath, setSdlcPath] = useState(initialPath);
  const [repoUrl, setRepoUrl] = useState(initialRepoUrl);
  const [repoBranch, setRepoBranch] = useState(initialRepoBranch);
  const [repoPath, setRepoPath] = useState(initialRepoPath);
  const [accessToken, setAccessToken] = useState("");
  const [loading, setLoading] = useState(false);
  // ...
}
```

**Source type toggle (two buttons):**

```tsx
<div className="flex gap-1 rounded-md bg-bg-elevated p-1">
  <button
    type="button"
    onClick={() => setSourceType("local")}
    className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
      sourceType === "local"
        ? "bg-bg-surface text-text-primary shadow-sm"
        : "text-text-tertiary hover:text-text-secondary"
    }`}
    data-testid="source-toggle-local"
  >
    Local
  </button>
  <button
    type="button"
    onClick={() => setSourceType("github")}
    className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
      sourceType === "github"
        ? "bg-bg-surface text-text-primary shadow-sm"
        : "text-text-tertiary hover:text-text-secondary"
    }`}
    data-testid="source-toggle-github"
  >
    GitHub
  </button>
</div>
```

**Conditional fields:**

```tsx
{sourceType === "local" ? (
  <div>
    <input
      type="text"
      placeholder="SDLC Path"
      value={sdlcPath}
      onChange={(e) => setSdlcPath(e.target.value)}
      required
      data-testid="input-sdlc-path"
      className="..."
    />
  </div>
) : (
  <>
    <div>
      <input
        type="text"
        placeholder="Repository URL"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        required
        data-testid="input-repo-url"
        className="..."
      />
    </div>
    <div>
      <input
        type="text"
        placeholder="Branch"
        value={repoBranch}
        onChange={(e) => setRepoBranch(e.target.value)}
        data-testid="input-repo-branch"
        className="..."
      />
    </div>
    <div>
      <input
        type="text"
        placeholder="Subdirectory Path"
        value={repoPath}
        onChange={(e) => setRepoPath(e.target.value)}
        data-testid="input-repo-path"
        className="..."
      />
    </div>
    <div>
      <input
        type="password"
        placeholder="Access Token (optional)"
        value={accessToken}
        onChange={(e) => setAccessToken(e.target.value)}
        data-testid="input-access-token"
        className="..."
      />
    </div>
  </>
)}
```

**Submit handler:**

```tsx
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  try {
    if (mode === "add") {
      const data: ProjectCreate = {
        name,
        source_type: sourceType,
      };
      if (sourceType === "local") {
        data.sdlc_path = sdlcPath;
      } else {
        data.repo_url = repoUrl;
        data.repo_branch = repoBranch;
        data.repo_path = repoPath;
        if (accessToken) {
          data.access_token = accessToken;
        }
      }
      await onSubmit(data);
      // Reset form fields
      setName("");
      setSdlcPath("");
      setRepoUrl("");
      setRepoBranch("main");
      setRepoPath("sdlc-studio");
      setAccessToken("");
    } else {
      const update: ProjectUpdate = {};
      if (name !== initialName) update.name = name;
      if (sourceType === "local" && sdlcPath !== initialPath) {
        update.sdlc_path = sdlcPath;
      }
      if (sourceType === "github") {
        if (repoUrl !== initialRepoUrl) update.repo_url = repoUrl;
        if (repoBranch !== initialRepoBranch) update.repo_branch = repoBranch;
        if (repoPath !== initialRepoPath) update.repo_path = repoPath;
        if (accessToken) update.access_token = accessToken;
      }
      await onSubmit(update);
    }
  } catch {
    // Error handled by parent via error prop
  } finally {
    setLoading(false);
  }
};
```

**Files:**
- `frontend/src/components/ProjectForm.tsx`

### Phase 3: ProjectCard Updates

**Goal:** Display source type badge and appropriate path information.

- [ ] Update `frontend/src/components/ProjectCard.tsx`:

```tsx
const SOURCE_BADGE: Record<string, { label: string; className: string }> = {
  local: {
    label: "Local",
    className: "bg-bg-elevated text-text-tertiary",
  },
  github: {
    label: "GitHub",
    className: "bg-accent/10 text-accent",
  },
};

// Inside the component JSX, after the name heading:
<div className="mt-1 flex items-center gap-2">
  <span
    className={`inline-flex rounded px-1.5 py-0.5 text-[10px] font-medium ${
      SOURCE_BADGE[project.source_type]?.className ?? SOURCE_BADGE.local.className
    }`}
    data-testid="source-badge"
  >
    {SOURCE_BADGE[project.source_type]?.label ?? "Local"}
  </span>
  <p className="truncate font-mono text-xs text-text-tertiary">
    {project.source_type === "github"
      ? project.repo_url
      : project.sdlc_path}
  </p>
</div>
```

**Files:**
- `frontend/src/components/ProjectCard.tsx`

### Phase 4: Settings Page Updates

**Goal:** Pass new initial props to ProjectForm when editing.

- [ ] Update `frontend/src/pages/Settings.tsx`:
  - When rendering the edit form, pass additional props:

```tsx
<ProjectForm
  mode="edit"
  initialName={editingProject.name}
  initialPath={editingProject.sdlc_path ?? ""}
  initialSourceType={editingProject.source_type}
  initialRepoUrl={editingProject.repo_url ?? ""}
  initialRepoBranch={editingProject.repo_branch}
  initialRepoPath={editingProject.repo_path}
  onSubmit={handleUpdate}
  onCancel={() => setEditingProject(null)}
  error={editError}
/>
```

**Files:**
- `frontend/src/pages/Settings.tsx`

### Phase 5: Testing and Validation

**Goal:** Component tests for toggle behaviour, conditional fields, and submission data.

- [ ] ProjectForm tests:

| # | Test | Description |
|---|------|-------------|
| 1 | `test_renders_source_toggle` | Both "Local" and "GitHub" buttons are visible |
| 2 | `test_local_mode_shows_sdlc_path` | Default mode shows SDLC Path input |
| 3 | `test_local_mode_hides_github_fields` | Default mode does not render repo URL input |
| 4 | `test_github_mode_shows_repo_fields` | Clicking "GitHub" shows Repository URL, Branch, Subdirectory, Token fields |
| 5 | `test_github_mode_hides_sdlc_path` | GitHub mode does not render SDLC Path input |
| 6 | `test_submit_local_data` | Submitting in local mode sends `{ name, source_type: "local", sdlc_path }` |
| 7 | `test_submit_github_data` | Submitting in GitHub mode sends `{ name, source_type: "github", repo_url, ... }` |
| 8 | `test_submit_github_no_empty_token` | Token field empty means `access_token` is not included in submission |
| 9 | `test_edit_mode_prepopulates_github` | Edit mode with GitHub initial props shows pre-filled values |
| 10 | `test_default_branch_and_path` | Branch defaults to "main", subdirectory to "sdlc-studio" |

- [ ] ProjectCard tests:

| # | Test | Description |
|---|------|-------------|
| 1 | `test_local_badge_displayed` | Local project shows "Local" badge |
| 2 | `test_github_badge_displayed` | GitHub project shows "GitHub" badge |
| 3 | `test_github_shows_repo_url` | GitHub project shows `repo_url` instead of `sdlc_path` |
| 4 | `test_local_shows_sdlc_path` | Local project shows `sdlc_path` |

- [ ] Verify TypeScript compilation: `cd frontend && npx tsc --noEmit`
- [ ] Run all frontend tests: `cd frontend && npx vitest run`

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `test_renders_source_toggle` | `ProjectForm.test.tsx` | Pending |
| AC2 | `test_local_mode_shows_sdlc_path` | `ProjectForm.test.tsx` | Pending |
| AC3 | `test_github_mode_shows_repo_fields` | `ProjectForm.test.tsx` | Pending |
| AC4 | `test_submit_local_data`, `test_submit_github_data` | `ProjectForm.test.tsx` | Pending |
| AC5 | `test_local_badge_displayed`, `test_github_badge_displayed` | `ProjectCard.test.tsx` | Pending |
| AC6 | `test_edit_mode_prepopulates_github` | `ProjectForm.test.tsx` | Pending |
| AC7 | `npx tsc --noEmit` passes | compilation check | Pending |

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | User switches toggle after filling fields | Field values preserved in state; switching back shows previously entered data | Phase 2 |
| 2 | Edit mode for local project (no GitHub fields) | GitHub fields get default initial values ("", "main", "sdlc-studio") | Phase 4 |
| 3 | Project with null sdlc_path (GitHub source) | ProjectCard shows `repo_url` instead; null-safe with `?? ""` | Phase 3 |
| 4 | Long repository URL in ProjectCard | `truncate` class clips with ellipsis | Phase 3 |
| 5 | Access token in edit mode | Token field is always empty (never pre-populated from masked value); only sent if user enters a new value | Phase 2 |
| 6 | Unknown source_type in ProjectCard | Falls back to "Local" badge styling | Phase 3 |

**Coverage:** 6/6 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing ProjectForm tests break | Medium | Update test fixtures to include default `source_type` values |
| ProjectCard layout shifts with badge | Low | Badge is small (10px font); tested visually in dev mode |
| Settings page not passing new props | Medium | TypeScript compiler catches missing required props |
| Tailwind alpha syntax for badge | Low | Use `/10` alpha syntax consistent with existing status badges |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Component tests written and passing (14 ProjectForm + 4 ProjectCard tests)
- [ ] TypeScript compilation passes (`npx tsc --noEmit`)
- [ ] Frontend tests pass (`npx vitest run`)
- [ ] Source toggle works in both add and edit modes
- [ ] GitHub fields have sensible defaults
- [ ] Access token field uses `type="password"`
- [ ] ProjectCard shows appropriate source badge

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Darren | Initial plan created |
