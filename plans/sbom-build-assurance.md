---
description: SBOM and SLSA build-provenance attestations for FtM's Python (PyPI + Docker) and TypeScript (npm) distribution channels, mirroring rigour PR #211. Java is intentionally out of scope.
date: 2026-05-27
tags: [ci, supply-chain, sbom, slsa, attestations]
---

# SBOM + build assurance for followthemoney

## Background

[rigour#211](https://github.com/opensanctions/rigour/pull/211) added two things to the rigour wheel pipeline:

1. **`cargo-auditable`** — embeds the full Cargo dep graph into the compiled `.so` so downstream SBOM scanners (`syft`, `cargo audit bin`) see transitive Rust crates instead of one opaque `rigour` blob.
2. **`actions/attest-build-provenance@v4`** — produces a SLSA-style attestation per artifact, verifiable via `gh attestation verify` and (on tagged releases) PEP 740 PyPI badges.

FtM is **pure Python**, so part 1 has no analog: there is no compiled binary that hides a private dep graph. A wheel's `METADATA` already lists every pinned Python dep, and `syft <wheel>` enumerates them out of the box.

## Framing: three libs in one folder

This repo really hosts three independent libraries that happen to share a tree:

| lib | what it is | where it ships | in scope? |
|-----|------------|----------------|-----------|
| **Python** | `followthemoney/` package | PyPI + `ghcr.io/opensanctions/followthemoney` Docker image | ✅ — primary focus |
| **TypeScript** | `js/` package | npm | ✅ |
| **Java** | `java/` package | Maven Central | ❌ — out of scope for this work |

Java is out of scope because Maven Central has no first-class surface for GitHub-side attestations the way PyPI's PEP 740 does, and the Java port has a different (smaller) consumer set. We can revisit later as a standalone PR.

## Goals

1. **Python on PyPI** carries a SLSA build-provenance attestation per published artifact (wheel + sdist), visible as a PEP 740 badge on PyPI and verifiable with `gh attestation verify`. This is the primary deliverable — PyPI is where FtM has the broadest installed base.
2. **Python Docker image** on `ghcr.io` carries both build-provenance and a CycloneDX SBOM attestation in the OCI registry, verifiable with `cosign verify-attestation` or `gh attestation verify oci://...`.
3. **TypeScript on npm** carries a build-provenance attestation on the published tarball.

## Scope per channel

### Python wheel + sdist (`python` job → split)

Two structural problems with the current job before attestations can attach cleanly:

- **Wheel is built inside the 3.11–3.14 matrix.** Right now `python3 -m build --wheel` runs four times. Pure-Python wheels are `py3-none-any` and identical across the matrix, so attesting inside the matrix produces 4 attestations of the same bytes (or races on publish). The wheel build needs to move into a dedicated job that depends on `python` (tests must pass first).
- **No sdist is built today** but the config is already in place. `pyproject.toml` has `[tool.hatch.build.targets.sdist]` with `only-include = ["followthemoney", "LICENSE", "README.md"]`, so someone set it up — the CI step just never built one. PyPI currently shows only `.whl`. Change `python3 -m build --wheel` → `python3 -m build` (one character) to build both. Worth a one-time local check that the resulting `.tar.gz` includes `followthemoney/schema/*.yaml` and translations, and that `pip install ./dist/followthemoney-*.tar.gz` works in a clean venv.

New `wheel` job, runs after `python`:
- Build wheel + sdist with `python3 -m build`.
- `actions/attest-build-provenance@v4` with `subject-path: 'dist/*'`.
- Existing `pypa/gh-action-pypi-publish@release/v1` moves into this job (still tag-gated). With recent action versions this auto-emits PEP 740 attestations on PyPI via the tokenless OIDC flow — to be visually confirmed on the next tagged release. If the badge doesn't appear, pin the action to `v1.11.0+`.

This is the **primary deliverable** of the PR — everything else is gravy.

### Python Docker image (`docker` job)

The largest opaque artifact and the one used in production. Highest-leverage place for an SBOM.

- Capture the pushed image digest from `docker/build-push-action@v7` (`outputs.digest`).
- `actions/attest-build-provenance@v4` with `subject-name: ghcr.io/opensanctions/followthemoney`, `subject-digest: ${{ steps.push.outputs.digest }}`, `push-to-registry: true`. Attestation lives in the OCI registry alongside the image, verifiable via `gh attestation verify oci://ghcr.io/opensanctions/followthemoney@sha256:...` or `cosign verify-attestation`.
- `anchore/sbom-action@v0` to generate a CycloneDX SBOM of the image filesystem (catches apt packages + everything in `/venv` — i.e. the Python deps actually resolved at build time, not just the version ranges in `pyproject.toml`).
- `actions/attest-sbom@v2` to attach the SBOM as a typed attestation alongside the provenance.
- Today the `docker` job runs on `main` and tags, but only *pushes* on tags. Attest only on the push path — pre-push builds aren't published anywhere, so attesting them is wasted effort.

### TypeScript on npm (`nodejs` job)

- Add a step after `npm run build` that produces a tarball via `npm pack` into a known path.
- `actions/attest-build-provenance@v4` with `subject-path: 'js/<tarball>.tgz'`.
- Change `npm publish` to take the tarball path (`npm publish ./<tarball>.tgz`) so the published bytes match what was attested. **This is a behavior change** from the current implicit-pack `npm publish` and is the only invasive bit on the npm side — verify the resulting tarball matches the current published shape before merging (compare `npm pack --dry-run` output to a recently published version).
- Worth knowing: npm registry has its own provenance mechanism (`npm publish --provenance`) which is a different attestation chain from GitHub's. Either is fine; `attest-build-provenance` is consistent with what we're doing on PyPI/Docker, so prefer that for symmetry.

## Workflow permissions

Add to the top-level `permissions:` block (already has `id-token: write`):

```yaml
attestations: write
artifact-metadata: write   # required by attest-build-provenance@v4
```

`packages: write` already exists for ghcr.io.

## Proposed structure

```
python      (matrix: 3.11–3.14)  — tests + typecheck only
  └─ wheel  (single)              — build, attest, publish to PyPI    ⭐ primary
nodejs                            — build, pack, attest, publish to npm
java                              — UNCHANGED (out of scope)
docker      (main + tags)         — build, push, attest provenance, attest SBOM
```

Each terminal job is independent — they can fan out in parallel.

## Implementation order

1. Permissions block — single line change. Has to land first or everything 403s.
2. **PyPI**: split wheel build out of the python matrix into its own job, add sdist, wire `attest-build-provenance`.
3. **Docker**: capture digest, attest provenance to the registry, add `sbom-action` + `attest-sbom`.
4. **npm**: `npm pack` + attest + adjust `npm publish` to take the tarball path.

Steps 2–4 are independent and can be reviewed/merged separately if we want smaller PRs. PyPI is the highest-value, lowest-risk one and should go first.

## Verification (test plan, post-merge)

- CI green on the PR.
- Repo **Attestations** tab shows entries for each artifact after a `main` push.
- `gh attestation verify <wheel> --owner opensanctions` passes locally on a downloaded wheel.
- `gh attestation verify oci://ghcr.io/opensanctions/followthemoney@sha256:<digest> --owner opensanctions` passes for the Docker image.
- On the next tagged release:
  - **PyPI shows PEP 740 attestation badges** next to `followthemoney-*.whl` and `.tar.gz`. (Primary success signal.)
  - `npm view followthemoney-data dist` shows the published tarball matches what was attested.
  - `ghcr.io` image manifest references the provenance + SBOM attestations.
- Downstream smoke check: `syft ghcr.io/opensanctions/followthemoney:<tag> -o cyclonedx-json` shows the same component list as our attached SBOM (sanity-check they agree).

## Decisions

- **sdist**: yes, publish one alongside the wheel. Config already exists in `pyproject.toml`; CI just needs the build flag changed.
- **SBOM on the wheel**: no. Wheel METADATA already enumerates transitive Python deps; an attached SBOM adds nothing. Docker-only.

## Non-goals / explicitly out of scope

- **Java / Maven Central** — see framing above. Separate PR if/when we want it.
- **`cargo-auditable` or equivalent** — no compiled binary in FtM, no information to embed.
- **`pip-audit` / `safety` in CI** — that's vuln scanning, not provenance. Separate concern.
- **Sigstore `cosign` signing of arbitrary artifacts** — `attest-build-provenance` already uses Sigstore under the hood.
- **Reproducible builds** — much bigger project, not what rigour did.
