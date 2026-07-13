# BG-01KXDGA1: No application log line ever reaches stdout: every logger call in the app is silently discarded

> **Status:** Fixed
> **Severity:** High
> **Verification depth:** functional
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Darren; human; v3
> **Triaged-by:** Priya Nair; persona; v3
> **Related:** CR-01KXCAZJ (the poller, whose entire safety story rests on its logs)

## Summary

**`logging.basicConfig` is never called anywhere in the application.** Uvicorn configures only its *own*
loggers (`uvicorn`, `uvicorn.access`, `uvicorn.error`); it does not touch the root logger. So the root
logger has no handler, and **every `logger.info` / `logger.warning` / `logger.exception` in
`sdlc_lens.*` is silently discarded.**

Confirmed in production on v0.6.0: the container's entire log output is Alembic, Uvicorn's own lines, and
access logs. Not one application line - despite `SDLC_LENS_LOG_LEVEL=INFO` being set, which does nothing
because nothing reads it.

What is being thrown away:

- **`"Freshness poller started"`**, and every poll failure. The poller is an unattended loop whose failure
  mode is *silence* - a task that dies takes freshness with it and says nothing. Its **only** observability
  is the log, and the log goes nowhere. The safety story I wrote for CR-01KXCAZJ is, in production, fiction.
- **`"Sync bug: ... needs a reparse but arrived with no content"`** and the blob-SHA mismatch error - the
  fail-loud branches added precisely so a silent corruption could not happen quietly.
- **`"Project ... was left mid-sync by a hard stop"`** (BG-01KXDFGD's reaper).
- **The plaintext-token security warning** - the one that tells an operator their GitHub PATs are
  unencrypted at rest. It has never once been seen.

## Steps to Reproduce

```
$ docker logs sdlc-studio-lens-app-1 | grep -i poller
$          # nothing

$ curl -s localhost:8035/api/v1/system/health
{"status":"healthy","version":"0.6.0","ready":true, ...}     # the app is fine
```

The app works. It simply cannot tell you anything.

## Root cause

`config.py` defines `log_level: str = "INFO"` and **nothing consumes it**. No `basicConfig`, no
`dictConfig`, no handler on the root logger. Every module does `logger = logging.getLogger(__name__)` and
logs into a void.

This is pre-existing - it has been true since the first commit - but it was harmless while the app was
request/response: a failure surfaced as a 500 and an error field on the project. The **poller** changes
that. It is the first component that runs unattended, forever, with no user watching a response, and whose
documented failure mode is "it stops quietly". For that component the log is not a nicety; it is the entire
mechanism by which a human ever learns something is wrong.

## Proposed Fix

Configure the root logger at application startup from `settings.log_level`, with a handler on stdout so
Docker captures it. Do not clobber Uvicorn's own handlers.

Then **prove it**: assert that a known application log line actually appears on stdout. A test that only
checks `caplog` proves nothing here - `caplog` installs its own handler, which is exactly why 819 tests
passed while the real application logged nothing at all. The test must exercise the configured root logger,
not a fixture that fakes one.

## Acceptance Criteria

- [x] `logger.info` from an `sdlc_lens.*` module reaches stdout when the app runs
- [x] `SDLC_LENS_LOG_LEVEL` actually takes effect (it previously did nothing)
- [x] Uvicorn's own access/error logs still work and are not duplicated
- [x] The poller's startup line and its failure warnings are visible in `docker logs`
- [x] Proven against the REAL configured logger, not `caplog` - the tests capture actual stdout
- [x] Mutation-checked: three mutants, three killed - removing `configure_logging()` from the factory; never adding the handler (the exact production state); and `if not root.handlers` instead of checking for OUR handler (the variant I nearly shipped, which would have gone silent again the moment anything else touched the root logger)
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_logging_reaches_stdout.py -q

## Lessons

- **A test fixture that supplies the thing under test proves nothing about production.** `caplog` attaches
  its own handler, so every logging assertion in 819 tests passed while the real application had no handler
  at all. The fixture was testing itself.
- **Observability is a feature, and it needs a test like any other.** "We log it" was stated in comments,
  docstrings, an AC and a retro - and it was never true.
- **A config setting nothing reads is a lie in a config file.** `log_level` has sat there since the first
  commit looking like it worked.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Found while verifying the v0.6.0 deploy: the poller's startup line was missing from `docker logs`, and then so was every other application log line. |
