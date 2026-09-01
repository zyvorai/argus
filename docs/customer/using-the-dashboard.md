# Using the Dashboard

Zyvor Argus’s **Mission Control** is a single live console at `/dashboard` (login at `/login` when password auth is on).

## Layout

| Element | Purpose |
|---------|---------|
| **Side rail** | Category navigation: Overview, Ask Zyra, Pipeline, Visual, Quality, Journeys, API, Probes, Security, Operations — collapsible to icons-only |
| **Global header** | Knowledge lamp, dark/light theme toggle, **Search** (opens ⌘K palette) |
| **Overview hero** | Health banner + stat tiles (pods, replicas, last run, pass rate, cron, knowledge) |
| **Panel viewport** | One active category at a time; hash URLs (`#pipeline`, `#ask`, …) are bookmarkable |
| **Workloads / Pods** | K8s strip and pod cards with log drawer (needs kube SA or kubeconfig) |
| **Action cards** | Job cards inside each category panel — smoke, flow, HAR, probes, security, … |
| **Live job panel** | macOS Terminal chrome — syntax-colored streaming log, case chips, Stop, copy/download log |
| **Operations** | Schedules, Findings, QA Runs, Videos |
| **Command palette** | ⌘K / Ctrl-K or header **Search** — jump to any action or Ask Zyra |

## Theme

Dark charcoal theme is the default (Apple-style, minimal blue accent buttons). Use the **moon/sun** control in the header to switch to light mode; preference persists in the browser. Login uses the same design system.

## Browse vs act

Reading pods, history, and findings is safe. Starting jobs mutates the target under test and writes reports under `reports/` — confirm URL, credentials, and scope before Run.

## Practice on zyvor.dev

See [Test zyvor.dev (with recording)](test-zyvor-dev.md) for smoke + flow video + HAR against the public site.

## Ask Zyra

Optional citation-first knowledge Q&A — side rail **Ask Zyra** or ⌘K. See [Tutorial 14](../tutorials/14-ask-zyra-knowledge.md).

## Related

- [Getting Started](getting-started.md)
- [Test zyvor.dev](test-zyvor-dev.md)
- [Page-by-page guides](pages/README.md)
- [Common workflows](workflows.md)

## Operate from the console (UX)

1. Open `/dashboard` (sign in at `/login` when auth is enabled).
2. Pick a category from the side rail or ⌘K.
3. Fill the action card fields, run the job, watch the live terminal panel.
4. Review Findings / QA Runs / downloads when the job completes.
5. **Empty / fail:** Check `GET /health`, auth, and that Playwright browsers are installed on the host.
