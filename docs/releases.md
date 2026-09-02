# Releases & Container Image

Tagged releases are published automatically by [`.github/workflows/release.yml`](../.github/workflows/release.yml).

**Current release:** [v0.9.2](https://github.com/zyvorai/argus/releases/tag/v0.9.2)

## What happens on a release

Pushing a tag matching `v*.*.*` (e.g. `v0.9.2`) to the [`zyvorai/argus`](https://github.com/zyvorai/argus) repo:

1. Builds the container image from [`docker/Dockerfile`](../docker/Dockerfile).
2. Pushes it to GHCR as `ghcr.io/zyvorai/zyvor-argus:<tag>` and `:latest`.
3. Builds the macOS desktop app (`desktop/`, on a `macos-latest` runner) and attaches the unsigned `.dmg` to the release.
4. Creates a GitHub Release on the tag with release notes.

## Desktop app

Download the `.dmg` from the [latest release](https://github.com/zyvorai/argus/releases/latest), unless you want to build it yourself (see [Tutorial 17](tutorials/17-desktop-app.md)). It's **unsigned** — macOS Gatekeeper will warn on first launch (right-click → Open). It also needs `argus` on your `PATH`, or point the app at a local checkout's `.venv/bin/argus` via Settings (⌘,). See `desktop/README.md`.

## Pulling the image

```bash
docker pull ghcr.io/zyvorai/zyvor-argus:v0.9.2
# or track latest
docker pull ghcr.io/zyvorai/zyvor-argus:latest

docker run --rm --env-file .env ghcr.io/zyvorai/zyvor-argus:v0.9.2 test
docker run --rm -p 8080:8080 --env-file .env ghcr.io/zyvorai/zyvor-argus:v0.9.2 serve --port 8080 --host 0.0.0.0
```

The image entrypoint is `argus`. Pass any subcommand as the container command.

Single Pod example:

```bash
kubectl run argus --image=ghcr.io/zyvorai/zyvor-argus:v0.9.2 \
  --env="ZYVOR_BASE_URL=https://zyvor.dev" \
  -- serve --port 8080 --host 0.0.0.0
```

The [`kubernetes/`](../kubernetes/README.md) manifests and k3s path in [`docs/remote-deploy.md`](remote-deploy.md) are optional — for managed Deployment/Service, not required to run the container.

GHCR packages inherit repo visibility — if the repo is private, `docker login ghcr.io` with `read:packages`.

## Cutting a release

```bash
# 1. Bump pyproject.toml + package.json to match the tag
# 2. Update CHANGELOG.md
git add -A && git commit -m "Release v0.9.2: …"
git tag v0.9.2
git push origin main
git push origin v0.9.2
gh release create v0.9.2 --repo zyvorai/argus --title "v0.9.2" --notes-file RELEASE_NOTES.md
```

The tag push triggers the release workflow (also `workflow_dispatch` with an existing tag to re-publish). See [CHANGELOG.md](../CHANGELOG.md).

## Verify after release

```bash
docker pull ghcr.io/zyvorai/zyvor-argus:v0.9.2
node scripts/e2e-remote-dashboard.mjs   # Chrome smoke against deployed Mission Control
```
