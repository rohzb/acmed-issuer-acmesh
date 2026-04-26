# Changelog

All notable changes to this project will be documented in this file.

## [0.2.2] - 2026-04-26

### Fixed
- Release workflow now resolves the plugin base image tag from the pinned
  `acmed-plugin-sdk` dependency instead of assuming it matches the issuer tag.
- This prevents GHCR build failures when issuer and SDK versions diverge.

## [0.2.1] - 2026-04-26

### Added
- Added addon installation of the `acme.sh` `dnsapi` bundle so DNS provider
  hooks are available at runtime.

### Changed
- Pinned addon installer default to `ACMESH_REF=v3.0.5` and made Docker build
  pass `ACMESH_REF` explicitly into addon install execution.

## [0.2.0] - 2026-04-25

### Added
- Functional remote acme.sh issuer plugin service with idempotent `order_id` result caching.
- Docker packaging for running plugin API service (`/healthz`, `/capabilities`, `/issue`).
- GitHub Actions CI and release workflows.

### Changed
- Docker image now builds as standalone repository context.
- ASGI app entrypoint is provided by installable package module
  (`acmed_issuer_acmesh.service:app`).
- README was rewritten for human-oriented project onboarding, operations, and troubleshooting.
- CI/release workflows were hardened with pinned core actions, release metadata
  validation, and gated release sequencing on successful CI runs.
- Docker image now extends `ghcr.io/rohzb/acmed-plugin-base-image:<tag>`,
  published by the `acmed-plugin-sdk` release workflow.
- CI/release workflows now pin Docker/publish/release actions to immutable
  SHAs and use valid optional PyPI publish gating.
