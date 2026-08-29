# Using the Dashboard

Zyvor Argus’s **Mission Control** is a single live console at `/dashboard` (login at `/login` when password auth is on).

## Surfaces

| Element | Purpose |
|---------|---------|
| **Boot splash** | Short warm-up intro on first load |
| **Hero** | Health banner + stat tiles (pods, replicas, last run, pass rate, cron) + primary Smoke CTA |
| **Signal field** | Live constellation canvas behind the hero |
| **Glass topbar / footer** | Sticky brand + status while you scroll |
| **Workloads / Pods** | K8s strip and pod cards with log drawer (needs kube SA or kubeconfig) |
| **Actions grid** | Every job card — smoke, flow, HAR, codegen, API, auth, vitals, probes, … |
| **Live job panel** | Streaming log, case chips, Stop, copy/download log |
| **Schedules** | Loop smoke / audit / ping / TLS / flow / sweep / API / realtime / vitals |
| **Findings** | Aggregated issues from quality jobs |
| **QA Runs / Videos** | History and recorded journeys |
| **Command palette** | ⌘K / Ctrl-K to find any action by name |

## UX extras

| Cue | How |
|-----|-----|
| **NOC wall** | Double-click the **Zyvor Mission Control** brand |
| **Warp flash** | Press `` ` `` or type `zyvor` |
| **Achievements** | First visit / NOC / warp unlock toast badges |
| **Reduced motion** | Splash / flash / canvas respect `prefers-reduced-motion` |

## Browse vs act

Reading pods, history, and findings is safe. Starting jobs mutates the target under test and writes reports under `reports/` — confirm URL, credentials, and scope before Run.

## Practice on zyvor.dev

See [Test zyvor.dev (with recording)](test-zyvor-dev.md) for smoke + flow video + HAR against the public site.

## Related

- [Getting Started](getting-started.md)
- [Test zyvor.dev](test-zyvor-dev.md)
- [Page-by-page guides](pages/README.md)
- [Common workflows](workflows.md)

## Operate from the console (UX)

1. Open this route from the nav or command palette and wait for live API data.
2. Use filters/search when present; drill into a row for detail.
3. For mutating actions: confirm role gates and impact before applying.
4. **Empty / fail:** Check service health, auth, and that required CRDs/backends for this domain are installed.
5. **Success:** Live data loads; created/updated objects appear without error toasts.

