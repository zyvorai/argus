# Tutorial 14 — Ask Zyra (knowledge RAG)

Grounded, citation-first answers about Zyvor products inside Mission Control. This is **optional** and separate from the Playwright test pipeline.

Requires **Python 3.11 or 3.12** (FastEmbed sparse retrieval).

## 1. Install extras

```bash
pip install -e ".[knowledge]"
cp .env.knowledge.example .env   # or merge into your existing .env
```

Set at least:

```env
LLM_API_KEY=...
LLM_MODEL=gpt-4o-mini
QDRANT_URL=http://localhost:6333
APP_API_KEY=change-me
```

For a local OpenAI-compatible endpoint, also set `LLM_BASE_URL` and matching `EMBEDDING_*` values.

## 2. Start Qdrant

```bash
docker compose -f docker/docker-compose.yml up -d qdrant
```

## 3. Ingest sample docs

```bash
argus ask ingest knowledge_docs/sample \
  --tenant-id public \
  --access-level public
```

Sample corpus includes manuals, migration guides, API reference, known issues, runbooks and a GitHub/code excerpt so specialised tools have distinct sources.
## 4. Serve Mission Control

```bash
argus serve --port 8080
```

Open `/dashboard` → **Ask Zyra**.

- Pick a product filter (e.g. PacketWolf)
- Ask: *How can PacketWolf allow namespace communication while blocking internet access?*
- Expect citations, confidence, and optional “insufficient context”
- Use **⧉ copy MD** for Slack/Jira; **New thread** for a fresh conversation
- ⌘K → “Ask Zyra” focuses the panel

The browser calls `POST /api/dashboard/ask` (session auth). Tenant and access levels come from server config (`KNOWLEDGE_TENANT_ID` / `KNOWLEDGE_ACCESS_LEVELS`), never from the client.

## 5. Direct API

```bash
curl -X POST http://localhost:8080/v1/qa \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me" \
  -H "X-Tenant-ID: public" \
  -d '{
    "question": "How can PacketWolf allow namespace communication while blocking internet access?",
    "product": "PacketWolf",
    "thread_id": "packetwolf-demo"
  }'
```

Health: `GET /v1/knowledge/health` or `GET /health` (includes a `knowledge` / `qdrant` field when extras are installed).

## 6. Evaluate

```bash
argus ask evaluate \
  --base-url http://localhost:8080 \
  --api-key change-me \
  --tenant-id public \
  --fail-under-keyword 0.5
```

The report includes HTTP success, citation rate, keyword score, citation precision,
groundedness proxy, abstention accuracy (when `expect_abstain` is set in the dataset),
and p50/p95 latency. Optional LangSmith tracing:

```bash
export LANGSMITH_API_KEY=...
argus ask evaluate --langsmith --base-url http://localhost:8080 --api-key change-me
```

## 7. Optional live cluster diagnostics

Opt in on the server (never mutates the cluster):

```env
ENABLE_LIVE_CLUSTER_TOOLS=true
KNOWLEDGE_LIVE_NAMESPACES=default,kube-system,rook-ceph
```

Ask Zyra can then combine docs with observed state via read-only tools such as
`get_cluster_summary`, `get_hubble_health`, `get_kubevirt_vm_status`,
`get_packetwolf_policy`, `get_vm_migration_status`, `get_guestkit_report`, and
`get_cilium_status`. Namespace queries outside the allowlist are denied. The
dashboard hint shows when live tools are enabled.

A **separate** remediation planner can be enabled with `ENABLE_REMEDIATION_AGENT=true`
(`POST /v1/remediation`, resume via `POST /v1/remediation/resume`). It uses human-in-the-loop
approval for restart requests. Set `ENABLE_REMEDIATION_EXECUTOR=true` plus namespace/prefix
allowlists to execute approved pod restarts; otherwise approval only records intent.

Ask Zyra streams progress over `POST /api/dashboard/ask/stream` (understanding → tool
calls → final answer) when `ENABLE_ASK_STREAMING=true`.

## Notes

- The agent uses specialised retrieval tools (manuals, API, GitHub, migration, known issues, runbooks) plus a broad fallback. Mission Control document-type filters still take precedence over tool defaults.
- Conversation `thread_id` values persist in SQLite (`KNOWLEDGE_CHECKPOINT_PATH`) across process restarts when that path is a file.
- PII middleware redacts emails and common API-token patterns from inputs/tool results. Set `LLM_FALLBACK_MODEL` for automatic model failover.
- Answers are read-only knowledge — the agent will not mutate cluster state. Live tools are also read-only when enabled.
- Re-ingesting a file deletes prior chunks for the same tenant + source path before indexing.
- Without `[knowledge]` extras, Mission Control still works; Ask Zyra shows offline / install hints.
