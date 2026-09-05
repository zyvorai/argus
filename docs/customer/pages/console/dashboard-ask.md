# Ask Zyra

## Purpose

Citation-first product knowledge Q&A — optional Qdrant hybrid RAG. Read-only; does not mutate cluster state. Aligned with **Zyra** copilot branding across the Zyvor platform.

## When to use it

- You need grounded answers from ingested manuals, API docs, runbooks, or migration guides
- You want citations and confidence scores before acting on an answer
- Live cluster diagnostics are optional (`ENABLE_LIVE_CLUSTER_TOOLS`) — still read-only

## How to get there

- Surface: `/dashboard/ask` · hash `#ask`
- UI: Mission Control → **Console** panel → **Ask Zyra** (side rail, or ⌘K → “Ask Zyra”)

## Operate from the console (UX)

1. Install optional extras: `pip install -e ".[knowledge]"`, start Qdrant, set `LLM_API_KEY` — see [Tutorial 14](../../../tutorials/14-ask-zyra-knowledge.md). For Ollama labs without an embeddings API, set `EMBEDDING_BACKEND=fastembed`.
2. Open **Ask Zyra**, pick product / document-type filters, ask a question.
3. Review citations, confidence badge, and **⧉ copy MD** for Slack/Jira.
4. Header **knowledge lamp** shows ready / degraded / offline.

Without `[knowledge]` extras, Mission Control still works; Ask Zyra shows offline with install hints.

## Related pages

- [Tutorial 14 — Ask Zyra](../../../tutorials/14-ask-zyra-knowledge.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
