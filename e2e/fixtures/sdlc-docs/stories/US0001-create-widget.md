# US0001: Create Widget

> **Status:** Done
> **Epic:** [EP0001: Alpha Feature](../epics/EP0001-alpha-feature.md)
> **Owner:** Alice
> **Priority:** High
> **Story Points:** 5
> **Created:** 2026-01-10

## User Story

**As a** platform user
**I want** to create a new widget with a name and type
**So that** I can track widgets in the system

## Acceptance Criteria

1. POST /api/v1/widgets creates a new widget
2. Name and type fields are required
3. Returns 201 with the created widget
4. Duplicate names return 409 Conflict
