# US0002: Update Widget

> **Status:** Done
> **Epic:** [EP0001: Alpha Feature](../epics/EP0001-alpha-feature.md)
> **Owner:** Alice
> **Priority:** Medium
> **Story Points:** 3
> **Created:** 2026-01-11

## User Story

**As a** platform user
**I want** to update an existing widget's properties
**So that** I can correct mistakes and change widget configuration

## Acceptance Criteria

1. PUT /api/v1/widgets/:id updates the widget
2. Partial updates are supported
3. Returns 404 if widget not found
