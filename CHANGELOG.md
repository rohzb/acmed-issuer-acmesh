# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-04-25

### Added
- Functional remote acme.sh issuer plugin service with idempotent `order_id` result caching.
- Docker packaging for running plugin API service (`/healthz`, `/capabilities`, `/issue`).
- GitHub Actions CI and release workflows.

### Changed
- Docker image now builds as standalone repository context.
- ASGI app entrypoint is provided by installable package module
  (`acmed_issuer_acmesh.service:app`).
