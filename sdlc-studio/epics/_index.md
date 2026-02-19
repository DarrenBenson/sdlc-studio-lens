# Epic Registry

**Last Updated:** 2026-02-19
**PRD Reference:** [Product Requirements Document](../prd.md)

## Summary

| Status | Count |
|--------|-------|
| Draft | 0 |
| Ready | 0 |
| Approved | 0 |
| In Progress | 0 |
| Done | 9 |
| **Total** | **9** |

## Epics

| ID | Title | Status | Owner | Stories | Points | Target |
|----|-------|--------|-------|---------|--------|--------|
| [EP0001](EP0001-project-management.md) | Project Management | Done | Darren | 5 | 16 | Phase 1 |
| [EP0002](EP0002-document-sync-and-parsing.md) | Document Sync & Parsing | Done | Darren | 6 | 24 | Phase 1 |
| [EP0003](EP0003-document-browsing.md) | Document Browsing | Done | Darren | 5 | 20 | Phase 2 |
| [EP0004](EP0004-dashboard-and-statistics.md) | Dashboard & Statistics | Done | Darren | 4 | 15 | Phase 2 |
| [EP0005](EP0005-search.md) | Search | Done | Darren | 3 | 12 | Phase 3 |
| [EP0006](EP0006-docker-deployment.md) | Docker Deployment | Done | Darren | 4 | 13 | Phase 3 |
| [EP0007](EP0007-git-repository-sync.md) | Git Repository Sync | Done | Darren | 5 | 18 | Phase 4 |
| [EP0008](EP0008-document-relationship-navigation.md) | Document Relationship Navigation | Done | Darren | 4 | 16 | Phase 5 |
| [EP0009](EP0009-project-health-check.md) | Project Health Check | Done | Darren | 3 | 13 | Phase 6 |

## By Phase

### Phase 1: Foundation (~40 points)

- **EP0001: Project Management** - Register projects, trigger sync, manage project list (~5 stories)
- **EP0002: Document Sync & Parsing** - Filesystem sync, blockquote parser, change detection, FTS5 indexing (~6 stories)

### Phase 2: Browsing & Dashboard (~35 points)

- **EP0003: Document Browsing** - Document list with filtering, rendered markdown viewer (~5 stories)
- **EP0004: Dashboard & Statistics** - Multi-project overview, completion metrics, progress charts (~4 stories)

### Phase 3: Search & Deployment (~25 points)

- **EP0005: Search** - Full-text search via FTS5, search UI, result filtering (~3 stories)
- **EP0006: Docker Deployment** - Dockerfiles, docker-compose, single container (~4 stories)

### Phase 4: Remote Sources (~18 points)

- **EP0007: Git Repository Sync** - GitHub API source, sync dispatch, conditional schemas (~5 stories)

### Phase 5: Navigation (~16 points)

- **EP0008: Document Relationship Navigation** - Relationship extraction, breadcrumbs, tree view (~4 stories)

### Phase 6: Quality (~13 points)

- **EP0009: Project Health Check** - Rules engine, health API, dashboard page (~3 stories)

## Dependency Graph

```
EP0001 (Project Management)
  └─► EP0002 (Document Sync & Parsing)
        ├─► EP0003 (Document Browsing)
        ├─► EP0004 (Dashboard & Statistics)
        └─► EP0005 (Search)

EP0001-EP0005 ─► EP0006 (Docker Deployment)
EP0001-EP0002 ─► EP0007 (Git Repository Sync)
EP0001-EP0003 ─► EP0008 (Document Relationship Navigation)
EP0001-EP0002, EP0008 ─► EP0009 (Project Health Check)
```

## Totals

| Phase | Epics | Story Points | Estimated Stories |
|-------|-------|--------------|-------------------|
| Phase 1 (Foundation) | EP0001, EP0002 | 40 | 11 |
| Phase 2 (Browsing & Dashboard) | EP0003, EP0004 | 35 | 9 |
| Phase 3 (Search & Deployment) | EP0005, EP0006 | 25 | 7 |
| Phase 4 (Remote Sources) | EP0007 | 18 | 5 |
| Phase 5 (Navigation) | EP0008 | 16 | 4 |
| Phase 6 (Quality) | EP0009 | 13 | 3 |
| **Total** | **9 epics** | **147** | **39** |

## Notes

- Epics are numbered globally (EP0001, EP0002, etc.)
- Stories are tracked separately in [Story Registry](../stories/_index.md)
- For PRD traceability, see the PRD Reference link in each Epic
- EP0001-EP0006 created from PRD Feature Inventory on 2026-02-17
- EP0007-EP0009 added retroactively on 2026-02-18/19
