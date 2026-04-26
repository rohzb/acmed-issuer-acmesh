"""acme.sh remote plugin handler.

The handler executes acme.sh directly inside the plugin service container and
returns normalized contract responses. It also caches terminal results by
`order_id` to keep retries idempotent.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from time import monotonic

from acmed_plugin_sdk.models import Capabilities, IssueRequest, IssueResult


class AcmeshPlugin:
    """acme.sh plugin handler implementation for remote mode."""

    def __init__(self) -> None:
        self._state_root = Path(os.environ.get("ACMED_PLUGIN_STATE_DIR", "/var/lib/acmed-plugin")) / "acmesh"
        self._state_root.mkdir(parents=True, exist_ok=True)

    def capabilities(self) -> Capabilities:
        return Capabilities(
            plugin_name="acmed-issuer-acmesh",
            plugin_version="0.2.0",
            challenge_modes=["dns-01", "http-01"],
        )

    def _order_dir(self, order_id: str) -> Path:
        path = self._state_root / "orders" / order_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _result_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "result.json"

    def _load_cached_result(self, order_id: str) -> IssueResult | None:
        path = self._result_path(order_id)
        if not path.exists():
            return None
        try:
            return IssueResult.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _save_cached_result(self, request: IssueRequest, result: IssueResult) -> None:
        self._result_path(request.order_id).write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _read_if_exists(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def _filtered_env(self, request: IssueRequest) -> dict[str, str]:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", "/tmp"),
        }
        profile = request.profile if isinstance(request.profile, dict) else {}
        for name in profile.get("credential_env", []):
            if isinstance(name, str) and name in os.environ:
                env[name] = os.environ[name]
        return env

    def _ensure_dnsapi_hooks(self, env: dict[str, str]) -> None:
        """Ensure acme.sh dnsapi hooks are available under the runtime HOME.

        acme.sh resolves DNS provider hooks from ``$HOME/.acme.sh/dnsapi``.
        Our image stages hook files under ``/usr/local/share/acme.sh/dnsapi``
        during build. This sync keeps runtime lookups functional for non-root
        users whose HOME is writable at runtime.
        """
        source_dir = Path("/usr/local/share/acme.sh/dnsapi")
        if not source_dir.exists():
            return

        home_dir = Path(env.get("HOME") or "/tmp")
        target_dir = home_dir / ".acme.sh" / "dnsapi"
        target_dir.mkdir(parents=True, exist_ok=True)

        for source_entry in source_dir.iterdir():
            target_entry = target_dir / source_entry.name
            if source_entry.is_dir():
                target_entry.mkdir(parents=True, exist_ok=True)
                continue
            if target_entry.exists():
                continue
            shutil.copy2(source_entry, target_entry)

    def issue(self, request: IssueRequest) -> IssueResult:
        cached = self._load_cached_result(request.order_id)
        if cached is not None:
            return cached

        started = monotonic()
        profile = request.profile if isinstance(request.profile, dict) else {}
        challenge_mode = str(profile.get("challenge_mode") or "dns-01")
        plugin_name = str(profile.get("plugin_name") or "").strip()
        directory_url = str(profile.get("ca_directory_url") or "").strip()

        if challenge_mode != "dns-01":
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="validation_error",
                command="acme.sh --issue",
                exit_code=64,
                stderr=f"unsupported acme.sh challenge_mode: {challenge_mode}",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result
        if not plugin_name:
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="validation_error",
                command="acme.sh --issue",
                exit_code=64,
                stderr="acme.sh remote issue requires profile.plugin_name",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        acmesh = str(profile.get("executable") or shutil.which("acme.sh") or "")
        if not acmesh:
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="dependency_missing",
                command="acme.sh --version",
                exit_code=127,
                stderr="acme.sh is not installed in plugin container",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        workdir = self._order_dir(request.order_id)
        cert_path = workdir / "certificate.pem"
        chain_path = workdir / "chain.pem"
        fullchain_path = workdir / "fullchain.pem"
        key_path = workdir / "private.key"

        issue_argv = [
            acmesh,
            "--issue",
            "--dns",
            plugin_name,
        ]
        if directory_url:
            issue_argv.extend(["--server", directory_url])
        for dns_name in request.dns_names:
            issue_argv.extend(["-d", dns_name])

        env = self._filtered_env(request)
        self._ensure_dnsapi_hooks(env)

        try:
            issue_run = subprocess.run(  # noqa: S603
                issue_argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=int(profile.get("timeout_seconds") or 120),
                cwd=str(workdir),
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            result = IssueResult(
                success=False,
                result_code="retryable_error",
                reason_code="timeout",
                command=" ".join(issue_argv),
                exit_code=124,
                stderr=f"acme.sh issue timeout: {exc}",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        if issue_run.returncode != 0:
            stderr = issue_run.stderr or ""
            reason_code = "dependency_failed"
            if "rate" in stderr.lower() and "limit" in stderr.lower():
                reason_code = "rate_limited"
            if "unauthorized" in stderr.lower() or "rejected" in stderr.lower():
                reason_code = "upstream_ca_error"
            result = IssueResult(
                success=False,
                result_code="retryable_error" if reason_code == "rate_limited" else "issuer_error",
                reason_code=reason_code,
                command=" ".join(issue_argv),
                exit_code=issue_run.returncode,
                stdout=issue_run.stdout,
                stderr=stderr,
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        install_argv = [
            acmesh,
            "--install-cert",
            "-d",
            request.common_name or request.dns_names[0],
            "--cert-file",
            str(cert_path),
            "--key-file",
            str(key_path),
            "--ca-file",
            str(chain_path),
            "--fullchain-file",
            str(fullchain_path),
        ]
        try:
            install_run = subprocess.run(  # noqa: S603
                install_argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=int(profile.get("timeout_seconds") or 120),
                cwd=str(workdir),
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            result = IssueResult(
                success=False,
                result_code="retryable_error",
                reason_code="timeout",
                command=" ".join(install_argv),
                exit_code=124,
                stdout=issue_run.stdout,
                stderr=f"acme.sh install timeout: {exc}",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        cert = self._read_if_exists(cert_path)
        chain = self._read_if_exists(chain_path)
        fullchain = self._read_if_exists(fullchain_path)
        key = self._read_if_exists(key_path)
        missing = []
        if cert is None:
            missing.append("certificate.pem")
        if fullchain is None:
            missing.append("fullchain.pem")
        if key is None:
            missing.append("private.key")

        stderr = "\n".join([piece for piece in [issue_run.stderr, install_run.stderr] if piece]).strip()
        stdout = "\n".join([piece for piece in [issue_run.stdout, install_run.stdout] if piece]).strip()
        if install_run.returncode != 0 or missing:
            if missing:
                stderr = "\n".join(
                    [piece for piece in [stderr, f"issuer output missing required artifacts: {', '.join(missing)}"] if piece]
                )
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="upstream_ca_error" if install_run.returncode != 0 else "internal_error",
                command=" && ".join([" ".join(issue_argv), " ".join(install_argv)]),
                exit_code=install_run.returncode if install_run.returncode != 0 else 65,
                stdout=stdout,
                stderr=stderr,
                certificate_pem=cert,
                chain_pem=chain,
                fullchain_pem=fullchain,
                private_key_pem=key,
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        result = IssueResult(
            success=True,
            result_code="issued",
            reason_code="ok_issued",
            command=" && ".join([" ".join(issue_argv), " ".join(install_argv)]),
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            certificate_pem=cert,
            chain_pem=chain,
            fullchain_pem=fullchain,
            private_key_pem=key,
            duration_ms=int((monotonic() - started) * 1000),
        )
        self._save_cached_result(request, result)
        return result
