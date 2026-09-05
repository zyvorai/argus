# Requirements impact

## Purpose

Impact view — shared data models & flows, co-occurrence edges, and typed Order → Payment dependencies with SVG canvas.

## When to use it

- You want to see which requirements share an entity (e.g. `Order`)
- You care about explicit “A depends on B” relationships named in specs
- You’re reviewing what a change to a model or flow might touch

## How to get there

- Surface: `/dashboard/requirements/impact` · hash `#requirements`
- UI: Mission Control → **Requirements** panel → **Impact — shared data models & flows**
- API: `GET /api/v2/requirements/impact-graph` (returns `data_models`, `flows`,
  `model_edges`, `model_dependencies`)

## What you can do

1. Open `/dashboard` (sign in at `/login` when `DASHBOARD_PASSWORD` is set).
2. Open **Requirements** and scroll to **Impact**.
3. Browse **By data model**, **Model edges** (co-occurrence), **Typed
   dependencies** (directed edges + canvas), and **By flow**.
4. Click a requirement id to open its detail drawer (quality score, issues,
   version history, linked tests).

Entities are extracted during `evaluate_quality` (`agents/requirement_entities/`,
LLM or rule fallback). Typed edges come from language like “Order depends on
Payment” or the LLM’s `model_dependencies` output (schema v6).

## Related pages

- [Requirements](dashboard-requirements.md)
- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
