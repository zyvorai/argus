# Zyvor Argus Mission Control — KT tutorial pipeline

Nine Playwright recordings driving the live Mission Control deployment,
stitched with the same ffmpeg title-card/caption composite pipeline as
`guestkit/scripts/demo-videos/` and `hypersdk-/scripts/demo-videos/`.

## Requirements

- `playwright` (symlinked `node_modules` — see below) with the `chrome` channel installed
- `ffmpeg` (needs `overlay`/`fade`/`concat`/`setpts` filters — captions are pre-rendered PNGs)
- `python3` (small float arithmetic in `build.sh`)
- A live Mission Control deployment (`ZQA_MC_URL`, default `http://175.110.122.71:30080`) —
  see `../deploy-remote.sh`

`node_modules` here is a symlink to a sibling project's `dashboard-react/node_modules`
(gitignored, not committed) — point it at any checkout with `playwright` installed.

## Recording

Mission Control runs **one job at a time**, so the segments must be recorded
sequentially, not in parallel:

```bash
node render-cards.mjs
node seg01-login.mjs       # -> raw/seg01-login/*.webm
node seg02-dashboard.mjs
node seg03-actions.mjs
node seg04-smoke.mjs       # real ~2.5 min live Smoke run, sped up 1.8x in the build
node seg05-flow.mjs
node seg06-audit.mjs       # real site audit against https://zyvor.dev
node seg07-probes.mjs
node seg08-ask.mjs
node seg09-noc.mjs
./build.sh                 # -> out/zyvor-argus-kt-tutorial.mp4
```

Override the target host/credentials with `ZQA_MC_URL` / `ZQA_MC_USER` / `ZQA_MC_PASS`
env vars (see `lib.mjs`) — defaults match the current lab deployment's
generated `.zyvor-argus-auth` credentials.

## Publishing

Not committed here (binary, per-run): copy finished MP4/GIF to `docs/assets/` for README and customer docs, following the regenerate steps in [`docs/assets/README.md`](../../docs/assets/README.md).
