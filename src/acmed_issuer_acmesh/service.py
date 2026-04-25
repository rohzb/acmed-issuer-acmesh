"""ASGI service entrypoint for the acme.sh issuer plugin."""

from __future__ import annotations

from acmed_plugin_sdk.server import PluginServerSettings, create_plugin_app

from .plugin import AcmeshPlugin

app = create_plugin_app(
    AcmeshPlugin(),
    settings=PluginServerSettings(require_bearer_auth=True),
)
