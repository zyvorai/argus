# Zyvor Argus customer PDFs

## Purpose

Generated: 2026-08-29
Rebuild: `node scripts/customer-docs/build-customer-pdfs.mjs`
- `ZyvorArgus-Customer-README.pdf` — Customer Documentation Overview
- `ZyvorArgus-Getting-Started.pdf` — Getting Started
- `ZyvorArgus-Admin-Basics.pdf` — Admin Basics
- `ZyvorArgus-Page-by-Page.pdf` — Page-by-Page Product Manual

## When to use it

- Open **Zyvor Argus customer PDFs** when the job matches this screen
- Prefer the product home / Get started panel if you are unsure where to begin
- Confirm health and auth tokens if probes fail

## How to get there

- UI path: `/ui/` → **Zyvor Argus customer PDFs** (or matching nav tab)
- Spotlight / in-app links when available

## Operate from the console (UX)

1. Open the Zyvor Argus UI (`/ui/`) on `https://<host>:…` (see Admin basics for the default port).
2. Navigate to **Zyvor Argus customer PDFs**.
3. Complete the on-screen fields / actions for this surface (Generated: 2026-08-29
Rebuild: `node scripts/customer-docs/build-customer-pdfs.mjs`
- `ZyvorArgus-Customer-README.pdf` —…).
4. Use **Probe** / **Save** / **Send** (or the primary button on the page) and watch status chips.
5. **Empty / fail:** Check Admin basics env vars, JWT/`API_TOKEN`, TLS insecure for lab certs, and backend reachability.
6. **Success:** Status shows healthy / accepted; related Lab or Logs surfaces reflect the change.

Never publish lab IPs — use `<host>`.

## Related pages

- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Admin basics](../../admin-basics.md)
- [Page index](../../PAGE_INDEX.md)
