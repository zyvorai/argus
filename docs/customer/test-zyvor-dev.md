# Test zyvor.dev (with recording)

Canonical how-to for pointing Zyvor Argus at **[https://zyvor.dev](https://zyvor.dev)**. **Watch the journey video first**, then re-run the same flow locally.

## Watch the recording

[![Zyvor Argus · Mission Control → GuestKit](https://img.youtube.com/vi/ys7SvKKqf9w/maxresdefault.jpg)](https://youtu.be/ys7SvKKqf9w)

<video src="../assets/zyvor-dev-mission-control-demo.webm" controls width="720" title="zyvor.dev journey recording"></video>

- **YouTube (with thumbnail):** https://youtu.be/ys7SvKKqf9w
- **[Download the .webm](../assets/zyvor-dev-mission-control-demo.webm)**
- Steps used: [`zyvor-dev-demo.steps`](../assets/zyvor-dev-demo.steps) in `docs/assets/`
- Full tutorial: [Test zyvor.dev with recording](../tutorials/13-test-zyvor-dev-recording.md)

## Setup

```bash
# .env
ZYVOR_BASE_URL=https://zyvor.dev
```

## Re-run the same recording

```bash
argus test exec --grep @smoke
argus flow run https://zyvor.dev --steps docs/assets/zyvor-dev-demo.steps --video
```

Journey video lands under `reports/artifacts/flows/cli/journey.webm` (or Mission Control → 🎬 Videos).

## Mission Control

```bash
argus serve --port 8080
# → http://localhost:8080/dashboard
```

1. ▶ **Smoke**
2. 🎬 **Flow test** — URL `https://zyvor.dev`, paste [`zyvor-dev-demo.steps`](https://github.com/zyvorai/zyvor-argus/blob/main/docs/assets/zyvor-dev-demo.steps), **record video** on
3. 📼 **HAR** — optional record `/` then replay

### UX cues

| Cue | How |
|-----|-----|
| Boot splash | Brief intro on first load |
| Signal field | Live constellation behind the hero |
| ⌘K | Command palette |
| NOC wall | Double-click the brand |
| Warp | `` ` `` or type `zyvor` |

## Related

- [Getting Started](getting-started.md)
- [Using the Dashboard](using-the-dashboard.md)
- [Flow test](pages/journeys/dashboard-actions-flow.md)
- [Common workflows](workflows.md)

## Operate from the console (UX)

1. Open this route from the nav or command palette and wait for live API data.
2. Use filters/search when present; drill into a row for detail.
3. For mutating actions: confirm role gates and impact before applying.
4. **Empty / fail:** Check service health, auth, and that required CRDs/backends for this domain are installed.
5. **Success:** Live data loads; created/updated objects appear without error toasts.

