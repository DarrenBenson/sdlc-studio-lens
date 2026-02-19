# TS0001: Create Widget Tests

> **Status:** Draft
> **Epic:** [EP0001: Alpha Feature](../epics/EP0001-alpha-feature.md)
> **Created:** 2026-01-10
> **Last Updated:** 2026-01-10

## Overview

Test specification for US0001 - Create Widget. Covers the POST endpoint including successful creation, validation errors, and duplicate detection.

## Test Cases

### TC0001: Successful widget creation
- **Given** valid widget data
- **When** POST /api/v1/widgets is called
- **Then** returns 201 with widget data

### TC0002: Duplicate name rejected
- **Given** a widget with name "Alpha" exists
- **When** POST /api/v1/widgets with name "Alpha"
- **Then** returns 409 Conflict
