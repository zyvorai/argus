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

import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const CUSTOMER = resolve(ROOT, 'docs/customer')
const SITE = resolve(process.argv[2] ?? resolve(ROOT, '../hypersdk-web'))
const PRODUCT = process.env.CUSTOMER_DOCS_PRODUCT || 'Zyvor Argus'
const SLUG = (process.env.CUSTOMER_DOCS_SLUG || 'zyvor-argus').toLowerCase().replace(/\s+/g, '-')
const PDF_PREFIX = process.env.CUSTOMER_DOCS_PDF_PREFIX || 'ZyvorArgus'
const MANUAL_DIR = process.env.CUSTOMER_DOCS_MANUAL_DIR || `${SLUG}-manual`
const TARGET = join(SITE, `docs/${MANUAL_DIR}`)
const PDF_TARGET = join(SITE, `static/downloads/${SLUG}-docs`)

if (!existsSync(join(SITE, 'docusaurus.config.ts'))) {
  console.error(`ERROR: ${SITE} is not hypersdk-web`)
  process.exit(1)
}

const TOP_LEVEL_POSITION = {
  'index.md': 1,
  'which-product.md': 2,
  'install-prerequisites.md': 3,
  'getting-started.md': 4,
  'using-the-dashboard.md': 5,
  'test-zyvor-dev.md': 6,
  'workflows.md': 7,
  'admin-basics.md': 8,
  'enterprise-sso.md': 9,
  'page-index.md': 10,
}

const REPO_ONLY = new RegExp(
  [
    '(\\.\\./)+(handbook|guides|architecture|admin-guide|user-guide|getting-started|developer-guide|legal|client)/',
    `${SLUG}-customer-feature-guide`,
    'zyvor-argus-customer-feature-guide',
    '(\\.\\./)+(architecture|configuration|troubleshooting|remote-deploy|test-authoring|releases|tutorials)/',
    'DEPLOYMENT_GUIDE',
    'AIRGAP_INSTALL',
    'CLI_GUIDE',
  ].join('|'),
)

function renameTarget(p) {
  return p.replace(/(^|\/)README\.md/, '$1index.md').replace(/(^|\/)PAGE_INDEX\.md/, '$1page-index.md')
}

function transformLinks(md) {
  return md
    .replace(/\[([^\]]*)\]\(([^)]+)\)/g, (full, text, target) => {
      const t = target.trim()
      if (/^(https?:|mailto:|#)/.test(t)) return full
      if (REPO_ONLY.test(t)) return text
      return `[${text}](${renameTarget(t)})`
    })
    .replaceAll('../assets/zyvor-dev-mission-control-demo.webm', `/downloads/${SLUG}-docs/zyvor-dev-mission-control-demo.webm`)
    .replaceAll('../assets/zyvor-dev-demo.steps', `/downloads/${SLUG}-docs/zyvor-dev-demo.steps`)
}

function rewriteIndexPdfSection(md) {
  const pdfNames = [
    `${PDF_PREFIX}-Customer-README`,
    `${PDF_PREFIX}-Getting-Started`,
    `${PDF_PREFIX}-Page-by-Page`,
    `${PDF_PREFIX}-Admin-Basics`,
  ]
  let out = md.replace(
    /```bash\nnode scripts\/customer-docs\/build-customer-pdfs\.mjs\n```\n\nOutput lands in \[`pdf\/`\]\(pdf\/\):/,
    'Prefer paper or offline reading? Download the print-ready PDFs:',
  )
  for (const name of pdfNames) {
    const nice = name.replace(`${PDF_PREFIX}-`, '').replace(/-/g, ' ')
    out = out.replaceAll(`\`${name}.pdf\``, `[${nice} (PDF)](/downloads/${SLUG}-docs/${name}.pdf)`)
  }
  return out
    .replace(/\nThe build regenerates indexes[^\n]*\n/, '\n')
    .replace(/\nCheck links with[^\n]*\n/, '\n')
    .replace(/\nPublish to the product site:\n\n```bash\nnode scripts\/customer-docs\/sync-to-website\.mjs[^\n]*\n```\n/, '\n')
    .replace(/\nAlso available:[^\n]*\n/, '\n')
}

function frontMatter(fields) {
  const lines = ['---']
  for (const [k, v] of Object.entries(fields)) lines.push(`${k}: ${typeof v === 'string' ? JSON.stringify(v) : v}`)
  lines.push('---', '', '')
  return lines.join('\n')
}

function walk(dir) {
  const out = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) out.push(...walk(full))
    else out.push(full)
  }
  return out
}

rmSync(TARGET, { recursive: true, force: true })
mkdirSync(TARGET, { recursive: true })
mkdirSync(PDF_TARGET, { recursive: true })

let written = 0
for (const file of walk(CUSTOMER)) {
  const rel = relative(CUSTOMER, file)
  if (rel.startsWith('pdf/') || !rel.endsWith('.md')) continue
  const target = join(TARGET, renameTarget(rel))
  mkdirSync(dirname(target), { recursive: true })
  let body = transformLinks(readFileSync(file, 'utf8'))
  const targetName = renameTarget(rel)
  if (targetName === 'index.md') {
    body = rewriteIndexPdfSection(body)
    body = frontMatter({ title: `${PRODUCT} Manual`, sidebar_position: 1, slug: `/${MANUAL_DIR}` }) + body
  } else if (targetName === 'pages/index.md') {
    body = frontMatter({ title: 'Page-by-page guides', sidebar_position: 1 }) + body
  } else if (TOP_LEVEL_POSITION[targetName]) {
    body = frontMatter({ sidebar_position: TOP_LEVEL_POSITION[targetName] }) + body
  }
  writeFileSync(target, body)
  written++
}

writeFileSync(
  join(TARGET, 'pages/_category_.json'),
  JSON.stringify({ label: 'Page-by-page guides', position: 6, collapsed: true, key: `${MANUAL_DIR}-pages` }, null, 2) + '\n',
)

const pagesDir = join(TARGET, 'pages')
if (existsSync(pagesDir)) {
  let i = 2
  for (const dir of readdirSync(pagesDir).sort()) {
    const full = join(pagesDir, dir)
    if (!statSync(full).isDirectory()) continue
    const label = dir.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    writeFileSync(join(full, '_category_.json'), JSON.stringify({ label, position: i++, collapsed: true, key: `${MANUAL_DIR}-pages-${dir}` }, null, 2) + '\n')
  }
}

let pdfs = 0
const pdfDir = join(CUSTOMER, 'pdf')
if (existsSync(pdfDir)) {
  for (const f of readdirSync(pdfDir)) {
    if (!f.endsWith('.pdf')) continue
    cpSync(join(pdfDir, f), join(PDF_TARGET, f))
    pdfs++
  }
}

// Demo journey video + steps (from docs/assets, not under gitignored reports/)
const assetsDir = resolve(ROOT, 'docs/assets')
const demoAssets = ['zyvor-dev-mission-control-demo.webm', 'zyvor-dev-demo.steps']
let demos = 0
for (const name of demoAssets) {
  const src = join(assetsDir, name)
  if (!existsSync(src)) continue
  cpSync(src, join(PDF_TARGET, name))
  demos++
}

console.log(`Synced ${written} markdown files -> ${TARGET}`)
console.log(`Copied ${pdfs} PDFs -> ${PDF_TARGET}`)
if (demos) console.log(`Copied ${demos} demo assets -> ${PDF_TARGET}`)
