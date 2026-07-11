# BG-01KX95WX: Stored XSS in search results: dangerouslySetInnerHTML on FTS snippet over synced document content

> **Status:** Fixed
> **Triaged-by:** Darren; human; v3
> **Severity:** High
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

SearchResults.tsx:175 renders `dangerouslySetInnerHTML={{ __html: item.snippet }}`. The snippet is the SQLite FTS5 `snippet(...)` over the raw document `content` column, stored verbatim at sync time with no HTML escaping. Since GitHub-repo sync (EP0007) means document bodies cross an external trust boundary, a synced .md whose body contains markup injects arbitrary HTML into the app origin when it appears in search results. Single-user LAN tool limits payoff, but it yields script execution in-origin (call the local API to delete projects, read other projects' `repo_url`/masked tokens, pivot on the LAN).

## Steps to Reproduce

Register/sync a repo whose a .md body contains an HTML/script payload; search for a term in that doc; the snippet's markup executes via innerHTML.

## Proposed Fix

Do not pass document-derived text through dangerouslySetInnerHTML. Escape the content before it enters the FTS index (and have snippet() wrap already-escaped text), OR return structured match ranges and render <mark> from escaped text in React, OR render {item.snippet} as plain text with the highlight reconstructed from known <mark> markers only.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
