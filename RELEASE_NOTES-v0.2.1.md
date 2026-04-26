# acmed-issuer-acmesh v0.2.1

Release date: 2026-04-26

## Summary

This patch release fixes DNS-hook availability for acme.sh DNS providers by
installing the full `dnsapi` bundle alongside the acme.sh executable.

## Highlights

- Addon install now downloads and installs `dnsapi` scripts into
  `/usr/local/share/acme.sh/dnsapi`.
- Docker build now passes `ACMESH_REF` explicitly to addon install.
- Default acme.sh reference remains pinned to `v3.0.5`.

## Compatibility

- Backward-compatible patch release.
- No API schema or HTTP contract changes.

## Operational impact

- DNS plugins such as `dns_hetznercloud` become available when using this
  updated image build flow.
