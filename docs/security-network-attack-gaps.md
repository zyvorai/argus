# Network-attack testing gaps

Argus ships an **authorized, engagement-gated** network-attack / DAST surface
on top of the earlier recon + sandboxed verification work. This page tracks
what is implemented versus what remains deliberately deferred.

## Implemented (this surface)

| Job kind | Tier / opt-in | Capability |
|----------|---------------|------------|
| `port_scan` | `active_recon` | Bounded TCP connect on ≤64 common ports |
| `tls_cipher_scan` | `active_recon` | Protocol + negotiated cipher grading (flags RC4/DES/NULL/legacy TLS) |
| `dast_scan` | `exploit` + `ZYVOR_DAST_SCAN_ENABLED` | Aggregates headers, injection, CSRF, open-redirect; optional nuclei via `ZYVOR_DAST_NUCLEI_BIN` |
| `injection_scan` | same DAST opt-in | Bounded SQLi / reflected-XSS / path-traversal probes |
| `csrf_probe` | same | Target forms missing CSRF tokens; cookies missing SameSite |
| `ssrf_probe` | same | URL-like params probed with internal canaries |
| `auth_attack_scan` | same | JWT `alg=none` hygiene, cookie flags, login enum hints — **no** brute force |
| `idor_scan` | same | Adjacent numeric ID comparison (±N, capped) |

CLI: `argus guard port-scan|tls-cipher-scan|dast-scan|injection-scan|csrf-probe|ssrf-probe|auth-attack-scan|idor-scan`.
Mission Control cards live under the security engagements section.
Details: [Tutorial 18](tutorials/18-security-testing.md), [`ROADMAP.md`](../ROADMAP.md).

## Still deliberately deferred

| Item | Why |
|------|-----|
| Full-range port / masscan sweeps | Abuse risk; product stays bounded |
| Packet capture, MITM, TLS stripping, ARP | Network-pentest platform territory |
| DDoS / flood | Explicitly forbidden in PoC generation; `loadtest` stays capped |
| AD / Kerberos / LDAP / WinRM | Out of scope (see host pentest notes) |
| Lateral movement / persistence | Out of scope |
| Security jobs on MCP / Slack allowlists | Fail-closed chat surface |
| Credential stuffing / password spraying | Not part of `auth_attack_scan` |

## Related paths

- Probes: `agents/probes/{port_scan,tls_cipher_scan,dast_scan,injection_scan,csrf_probe,ssrf_probe,auth_attack_scan,idor_scan}.py`
- Jobs: `orchestrator/dashboard/jobs.py` (`DAST_KINDS`, `ELEVATED_RISK_KINDS`)
- Auth session QA (not attack fuzz): `playwright/scripts/auth-probe.mjs`
