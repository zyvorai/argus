# Releases & Container Image

Tagged releases are published automatically by [`.github/workflows/release.yml`](../.github/workflows/release.yml).

**Current release:** [v0.9.0](https://github.com/zyvorai/argus/releases/tag/v0.9.0)

## What happens on a release

Pushing a tag matching `v*.*.*` (e.g. `v0.5.0`) to the `hypersdk/zyvor-argus` repo:

1. Builds the container image from [`docker/Dockerfile`](../docker/Dockerfile).
2. Pushes it to GHCR as `ghcr.io/hypersdk/zyvor-argus:<tag>` and `:latest`.
3. Builds the macOS desktop app (`desktop/`, on a `macos-latest` runner) and attaches the unsigned `.dmg` to the release.
4. Creates a GitHub Release on the tag with auto-generated notes.

## Desktop app

Download the `.dmg` from the [latest release](https://github.com/hypersdk/zyvor-argus/releases/latest), unless you want to build it yourself (see [Tutorial 17](tutorials/17-desktop-app.md)). It's **unsigned** — macOS Gatekeeper will warn on first launch (right-click → Open). It also needs a `argus` install to actually wrap: either `argus` on your `PATH`, or point it at a local checkout's `.venv/bin/argus` via the app's Settings (⌘,) — the release build has no local checkout of its own to auto-detect, unlike a `make desktop-build` you run yourself inside this repo. See `desktop/README.md` for what it does and doesn't bundle.

## Pulling the image

```bash
docker pull ghcr.io/hypersdk/zyvor-argus:v0.4.0
# or track latest
docker pull ghcr.io/hypersdk/zyvor-argus:latest

docker run --rm --env-file .env ghcr.io/hypersdk/zyvor-argus:v0.4.0 test
```

The image entrypoint is `argus` (see [`docker/Dockerfile`](../docker/Dockerfile)); pass any `argus` subcommand as the container command, e.g. `serve --port 8080 --host 0.0.0.0`.

No k3s/Kubernetes cluster is required to run it — it's a normal container. A single Pod works fine against any existing cluster too:

```bash
kubectl run argus --image=ghcr.io/hypersdk/zyvor-argus:v0.4.0 \
  --env="ZYVOR_BASE_URL=https://zyvor.dev" \
  -- serve --port 8080 --host 0.0.0.0
```

The [`kubernetes/`](../kubernetes/README.md) manifests and the k3s path in [`docs/remote-deploy.md`](remote-deploy.md) are only for when you want a managed Deployment/Service, not a requirement.

GHCR packages inherit repo visibility by default — if the repo is private, `docker pull` requires `docker login ghcr.io` with a token that has `read:packages`.

## Cutting a release

```bash
# bump pyproject.toml / package.json first, then:
git tag v0.6.0
git push hypersdk v0.6.0
# or, to also create the GitHub Release explicitly:
gh release create v0.6.0 --repo hypersdk/zyvor-argus --generate-notes
```

Either the tag push or the `gh release create` triggers the workflow (it also accepts `workflow_dispatch` with an existing tag, for re-publishing an image without cutting a new release). Version numbers follow `pyproject.toml` / `package.json` (currently `0.6.0`); bump those alongside the tag. See [CHANGELOG.md](../CHANGELOG.md).
