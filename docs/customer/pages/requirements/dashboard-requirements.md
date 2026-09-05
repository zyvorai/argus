# Requirements

## Purpose

Versioned requirements the pipeline ingested — source (github/document/email/transcript/jira/diarize), quality score, named issues, linked tests, and version history (read-only).

## When to use it

- Review what the last pipeline run stored and how quality scored each item
- Open history when a requirement changed and linked tests may need review
- Jump into **Impact** for shared models, co-occurrence edges, and typed deps

## How to get there

- Surface: `/dashboard/requirements` · hash `#requirements`
- UI: Mission Control → **Requirements** panel (side rail, or ⌘K / Ctrl-K **Search**)
- APIs: `GET /api/v2/requirements`, `…/{id}`, `…/{id}/history`

## What you can do

1. Open `/dashboard` (sign in at `/login` when `DASHBOARD_PASSWORD` is set).
2. Browse the requirements list (title, source, version, quality score).
3. Click a row for description, quality issues, version history, and linked tests.
4. Use **Impact** on the same panel for shared models / flows / typed deps.

Requirements are written by the pipeline (`fetch → parse → evaluate_quality`),
not through this UI. Sources include GitHub, local documents/PDFs, `.eml` or
IMAP email, transcripts, Jira (JSON / REST / OAuth), and diarized meetings.

## Related pages

- [Requirements impact](dashboard-requirements-impact.md)
- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
