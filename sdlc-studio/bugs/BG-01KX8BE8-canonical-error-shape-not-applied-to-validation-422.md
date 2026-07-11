# BG-01KX8BE8: Canonical error shape not applied to validation (422) or unhandled (500) responses

> **Status:** Fixed
> **Depends on:** BG-01KX8B82
> **Triaged-by:** Darren; human; v3
> **Severity:** High
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

main.py `create_app()` registers no exception handlers. Pydantic 422s and any unexpected 500 return FastAPI's default {'detail':...} instead of the canonical {'error':{'code','message'}}. The frontend extractErrorMessage reads body.error.message and silently falls back, so the contract holds only on hand-written per-route try/except paths.

## Steps to Reproduce

POST an invalid body to any endpoint; response is {'detail':[...]} (422), not the canonical {'error':{'code','message'}} shape.

## Proposed Fix

Register `add_exception_handler(RequestValidationError`, ...) and a catch-all Exception handler in `create_app()` emitting {'error':{'code':'`VALIDATION_ERROR`'|'INTERNAL','message':...}}; centralise domain-exception handling instead of repeating JSONResponse per route.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
