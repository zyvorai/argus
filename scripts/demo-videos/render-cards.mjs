// Render title/caption PNG cards for the Zyvor Argus "15-minute KT" tutorial —
// blue/cyan Mission Control ops aesthetic matching the dashboard itself.
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "png");

function titleHtml(kicker, line1, line2) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;width:1920px;height:1080px;background:#050b16;
    background-image:radial-gradient(ellipse 60% 50% at 20% 0%, rgba(59,130,246,0.20), transparent 55%),
                      radial-gradient(ellipse 50% 45% at 85% 100%, rgba(34,211,238,0.12), transparent 55%);
    font-family:-apple-system,'SF Pro Text',Segoe UI,sans-serif;display:flex;align-items:center;justify-content:center;}
  .wrap{text-align:center;padding:0 200px;}
  .kicker{font-family:ui-monospace,'SF Mono',monospace;color:#38bdf8;letter-spacing:0.3em;font-size:24px;font-weight:700;margin-bottom:33px;text-transform:uppercase;}
  h1{color:#f4f7fc;font-size:64px;font-weight:800;letter-spacing:-0.02em;margin:0 0 27px;line-height:1.15;}
  p{color:#93a4bd;font-size:32px;font-weight:400;margin:0;line-height:1.5;max-width:1280px;}
  .rule{width:96px;height:5px;background:linear-gradient(90deg,#38bdf8,#3b82f6);margin:39px auto 0;border-radius:5px;}
  </style></head><body>
  <div class="wrap">
    ${kicker ? `<div class="kicker">${kicker}</div>` : ""}
    <h1>${line1}</h1>
    ${line2 ? `<p>${line2}</p>` : ""}
    <div class="rule"></div>
  </div>
  </body></html>`;
}

function captionHtml(text) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;width:1920px;height:220px;background:transparent;
    font-family:-apple-system,'SF Pro Text',Segoe UI,sans-serif;display:flex;align-items:center;justify-content:center;}
  .bar{width:1770px;background:rgba(5,11,22,0.90);border:1px solid rgba(56,189,248,0.28);border-radius:21px;
    padding:27px 45px;display:flex;align-items:center;gap:21px;box-shadow:0 18px 45px rgba(0,0,0,0.45);}
  .dot{width:14px;height:14px;border-radius:50%;background:#38bdf8;flex:none;box-shadow:0 0 15px #38bdf8;}
  .text{color:#f1f5f9;font-size:32px;font-weight:500;line-height:1.4;}
  </style></head><body>
  <div class="bar"><div class="dot"></div><div class="text">${text}</div></div>
  </body></html>`;
}

const cards = [
  { file: "t00-title", kicker: "ZYAIQAAGENT · KT SESSION", line1: "Mission Control, Start to Finish", line2: "A 15-minute knowledge transfer for the autonomous QA agent behind Zyvor." },
  { file: "t01-intro", kicker: "WHAT IT IS", line1: "One Console, 20+ QA Capabilities", line2: "Flow tests, API contracts, visual regression, security probes, and an AI knowledge agent — all live-streamed with CSV/HTML/PDF reports." },
  { file: "t02-login", kicker: "1", line1: "Signing In to Mission Control" },
  { file: "t03-dashboard", kicker: "2", line1: "The Status Hero & Fleet View" },
  { file: "t04-actions", kicker: "3", line1: "The Actions Panel — Run Anything" },
  { file: "t05-smoke", kicker: "4", line1: "Running the Smoke Suite Live" },
  { file: "t06-flow", kicker: "5", line1: "Flow Tests — One Journey, One Video" },
  { file: "t07-audit", kicker: "6", line1: "Site Audit — an A–F Grade" },
  { file: "t08-probes", kicker: "7", line1: "Network & Security Probes" },
  { file: "t09-ask", kicker: "8", line1: "Ask Zyra — Citation-First Q&A" },
  { file: "t10-noc", kicker: "9", line1: "NOC Wall Mode & the ⌘K Palette" },
  { file: "t11-outro", kicker: "", line1: "That's the tour — you're ready to run it yourself.", line2: "docs/tutorials · zyvor.dev" },
];

const captions = [
  { file: "cap-login", text: "Default credentials are generated per host and persisted in .zyvor-argus-auth — sign in once, session lasts 12h (30d with remember me)." },
  { file: "cap-status", text: "One glanceable verdict — pods, replicas, last QA run, and a countdown to the next scheduled smoke run." },
  { file: "cap-pods", text: "Click any pod to open the live log drawer — last 100 lines, auto-refreshing, hover to pause." },
  { file: "cap-actions", text: "Every CLI command plus web-quality, security, and performance checks — click a card, one job runs at a time." },
  { file: "cap-smoke", text: "Live-streamed output, per-test ✓/✗ chips, a running tally, and a Stop button that kills the run mid-flight." },
  { file: "cap-flow", text: "A flow test drives a full user journey as one continuous Playwright session — recorded end-to-end as a single video." },
  { file: "cap-flow-steps", text: "Every step gets its own pass/fail row, correlated to the exact moment in the recording." },
  { file: "cap-audit", text: "Accessibility, SEO, performance, and security per page — rolled up into one letter grade." },
  { file: "cap-reports", text: "Every run exports to CSV, HTML, or a print-ready PDF — for a ticket, a standup, or an audit trail." },
  { file: "cap-probes", text: "Ten network & security probes — headers, cookies, CORS, compression, exposed paths, redirects — no browser required." },
  { file: "cap-ask", text: "Ask Zyra answers from the product's own knowledge base — citation-first, so every claim traces back to a real doc." },
  { file: "cap-noc", text: "Side rail collapses to icons-only — a compact view for narrow screens or NOC displays." },
  { file: "cap-palette", text: "⌘K opens the command palette — jump to any action without leaving the keyboard." },
];

const browser = await chromium.launch({ channel: "chrome" });

for (const t of cards) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.setContent(titleHtml(t.kicker, t.line1, t.line2));
  await page.screenshot({ path: `${outDir}/${t.file}.png` });
  await page.close();
  console.log("title:", t.file);
}

for (const c of captions) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 220 } });
  await page.setContent(captionHtml(c.text));
  await page.screenshot({ path: `${outDir}/${c.file}.png`, omitBackground: true });
  await page.close();
  console.log("caption:", c.file);
}

await browser.close();
