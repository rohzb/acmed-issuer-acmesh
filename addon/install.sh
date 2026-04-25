#!/usr/bin/env sh
set -eu
ACMESH_REF="${ACMESH_REF:-v3.0.5}"
curl --fail --show-error --silent --location \
  "https://raw.githubusercontent.com/acmesh-official/acme.sh/${ACMESH_REF}/acme.sh" \
  --output /usr/local/bin/acme.sh
chmod 0555 /usr/local/bin/acme.sh
