#!/usr/bin/env node
// Copyright 2026 ZyvorAI Labs Private Limited
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const PAGES = resolve(ROOT, 'docs/customer/pages')
const { routes } = JSON.parse(readFileSync(resolve(ROOT, 'scripts/customer-docs/routes.json'), 'utf8'))
const purposes = JSON.parse(readFileSync(resolve(ROOT, 'scripts/customer-docs/page-purposes.json'), 'utf8'))
const PRODUCT = process.env.CUSTOMER_DOCS_PRODUCT || 'Zyvor Argus'

function catDir(category) {
  return category.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'other'
}
function slug(path) {
  return path.replace(/^\//, '').replace(/\//g, '-').replace(/:/g, '') || 'home'
}

function guideTemplate({ title, path, category, purpose }) {
  return `# ${title}

## Purpose

${purpose}

## When to use it

- Open this card when the job matches the purpose above
- Prefer **Mission Control** (\`/dashboard\`) and the **⌘K** command palette if you are unsure where to start
- Confirm \`ZYVOR_BASE_URL\`, dashboard auth, and that Playwright browsers are installed if runs fail immediately

## How to get there

- Surface: \`${path}\`
- UI: Mission Control → **${category}** panel → **${title}** (side rail, or ⌘K / Ctrl-K **Search**)

## What you can do

1. Open \`/dashboard\` (sign in at \`/login\` when \`DASHBOARD_PASSWORD\` is set).
2. Fill the card fields for **${title}**, then start the action and watch the live job panel (✓/✗ chips, Stop, download log).
3. After success, check **Findings**, **QA Runs**, and any video / report links the card produces.
4. Turn recurring checks into a **Schedule** (5 min – 6 h) when you want continuous monitoring.

If the card stays idle or errors, hit \`GET /health\`, confirm the webhook/dashboard process is up (\`argus serve\`), and re-check env from [.env.example](../../../../.env.example).

## Related pages

- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
`
}

let written = 0
let skipped = 0
for (const r of routes) {
  const file = join(PAGES, catDir(r.category), `${slug(r.path)}.md`)
  mkdirSync(dirname(file), { recursive: true })
  if (existsSync(file)) {
    skipped++
    continue
  }
  writeFileSync(
    file,
    guideTemplate({
      title: r.label,
      path: r.path,
      category: r.category,
      purpose: purposes[r.path] || `${r.label} surface in ${PRODUCT} Mission Control.`,
    }),
  )
  written++
}
console.log(`Wrote ${written} guides (skipped existing ${skipped})`)
