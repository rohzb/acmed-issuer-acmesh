"""FastAPI entrypoint for acmed acme.sh plugin service."""

from __future__ import annotations

from acmed_plugin_sdk.server import PluginServerSettings, create_plugin_app
from acmed_issuer_acmesh.plugin import AcmeshPlugin

app = create_plugin_app(
    AcmeshPlugin(),
    settings=PluginServerSettings(require_bearer_auth=True),
)
