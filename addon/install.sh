#!/usr/bin/env sh
set -eu

ACMESH_REF="${ACMESH_REF:-v3.0.5}"

curl --fail --show-error --silent --location \
  "https://raw.githubusercontent.com/acmesh-official/acme.sh/${ACMESH_REF}/acme.sh" \
  --output /usr/local/bin/acme.sh
chmod 0555 /usr/local/bin/acme.sh

tmp_dir="$(mktemp -d)"
curl --fail --show-error --silent --location \
  "https://github.com/acmesh-official/acme.sh/archive/refs/tags/${ACMESH_REF}.tar.gz" \
  --output "${tmp_dir}/acme.sh.tar.gz"
tar -xzf "${tmp_dir}/acme.sh.tar.gz" -C "${tmp_dir}"
mkdir -p /usr/local/share/acme.sh
cp -a "${tmp_dir}"/acme.sh-*/dnsapi /usr/local/share/acme.sh/dnsapi
rm -rf "${tmp_dir}"
