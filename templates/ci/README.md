# CI templates

Copy-paste starting points for running `argus` as a QA gate in a CI system
other than GitHub Actions (which has its own reusable Action — see the repo's
[`action.yml`](../../action.yml)).

| File | CI system |
|---|---|
| `gitlab-ci.yml` | GitLab CI |
| `circleci-config.yml` | CircleCI |
| `Jenkinsfile` | Jenkins (declarative pipeline) |
| `azure-pipelines.yml` | Azure Pipelines |

All four run the published `ghcr.io/zyvorai/zyvor-argus` container image
directly — no Python/Node/Playwright setup steps needed in your own pipeline.
The `v0.9.1` tag in each template should track whichever release you've
pinned to; `:latest` also exists but isn't reproducible across runs.

For the full environment variable reference, exit-code contract, and the
`reports/summary.json` schema these templates rely on, see
[`docs/tutorials/15-external-cicd-integration.md`](../../docs/tutorials/15-external-cicd-integration.md).
