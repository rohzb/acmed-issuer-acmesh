# acmed-issuer-acmesh

Remote issuer plugin service that packages `acme.sh` tooling and exposes the
acmed plugin contract.

## Current status

- plugin API is implemented (`/healthz`, `/capabilities`, `/issue`)
- container addon installs `acme.sh`
- `/issue` executes `acme.sh --issue` and `acme.sh --install-cert`
- results are cached by `order_id` for idempotent retries

Runtime environment:

- `ACMED_REMOTE_PLUGIN_TOKEN` (required)
- `ACMED_REMOTE_PLUGIN_TOKEN_NEXT` (optional overlap token)
- `ACMED_PLUGIN_STATE_DIR` (optional, defaults to `/var/lib/acmed-plugin`)

## Build

Run from `upstream/acmed_gen2`:

```bash
docker build -f acmed-issuer-acmesh/docker/Dockerfile -t acmed-issuer-acmesh:0.2.0 .
```
