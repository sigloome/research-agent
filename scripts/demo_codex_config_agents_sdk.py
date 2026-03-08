#!/usr/bin/env python3
"""
Feasibility demo: can we bridge ~/.codex/config.toml into an OpenAI/Agents SDK runtime config?

This script is intentionally non-invasive:
- It only reads ~/.codex/config.toml.
- It does not mutate environment or files.
- It performs optional runtime checks if dependencies are installed.

Usage:
  python scripts/demo_codex_config_agents_sdk.py
  python scripts/demo_codex_config_agents_sdk.py \
    --base-url https://example.net/responses/bridge \
    --auth-header-name Byted-Authorization \
    --auth-header-value "Bearer <token>"
"""

from __future__ import annotations

import json
import os
import socket
import argparse
from pathlib import Path
from typing import Any


def load_toml(path: Path) -> dict[str, Any]:
    # Python 3.11+ has tomllib in stdlib.
    import tomllib  # pylint: disable=import-outside-toplevel

    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def pick_first(config: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        cur: Any = config
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return None


def can_resolve_host(host: str) -> tuple[bool, str]:
    try:
        ip = socket.gethostbyname(host)
        return True, ip
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None, help="Override OPENAI_BASE_URL")
    parser.add_argument(
        "--auth-header-name",
        default=None,
        help="Custom auth header name (e.g. Byted-Authorization)",
    )
    parser.add_argument(
        "--auth-header-value",
        default=None,
        help="Custom auth header value (e.g. Bearer xxxx)",
    )
    args = parser.parse_args()

    cfg_path = Path.home() / ".codex" / "config.toml"
    config = load_toml(cfg_path)

    # Heuristic key mapping from codex config into runtime env candidates.
    mapped = {
        "OPENAI_API_KEY": pick_first(
            config,
            [
                "openai.api_key",
                "api.openai_api_key",
                "auth.openai_api_key",
                "default.openai_api_key",
            ],
        ),
        "OPENAI_BASE_URL": pick_first(
            config,
            [
                "openai.base_url",
                "api.base_url",
                "default.base_url",
            ],
        ),
        "OPENAI_MODEL": pick_first(
            config,
            [
                "openai.model",
                "model",
                "default.model",
            ],
        ),
    }

    # Fall back to current environment values when config doesn't provide them.
    effective = {
        key: mapped.get(key) or os.getenv(key)
        for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")
    }
    if args.base_url:
        effective["OPENAI_BASE_URL"] = args.base_url

    custom_auth_header_name = (
        args.auth_header_name
        or os.getenv("OPENAI_AUTH_HEADER_NAME")
        or pick_first(config, ["openai.auth_header_name", "api.auth_header_name"])
    )
    custom_auth_header_value = (
        args.auth_header_value
        or os.getenv("OPENAI_AUTH_HEADER_VALUE")
        or pick_first(config, ["openai.auth_header_value", "api.auth_header_value"])
    )

    # Dependency checks.
    import importlib.util

    has_openai = importlib.util.find_spec("openai") is not None
    has_agents = importlib.util.find_spec("agents") is not None

    # Endpoint resolution checks.
    base = effective.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    host = base.split("://", 1)[-1].split("/", 1)[0]
    host_ok, host_info = can_resolve_host(host)

    report = {
        "config_path": str(cfg_path),
        "config_exists": cfg_path.exists(),
        "mapped_from_config": {k: bool(v) for k, v in mapped.items()},
        "effective_env_available": {k: bool(v) for k, v in effective.items()},
        "python_packages": {
            "openai": has_openai,
            "agents_sdk_import_name_agents": has_agents,
        },
        "auth": {
            "uses_openai_api_key": bool(effective.get("OPENAI_API_KEY")),
            "custom_auth_header_name": custom_auth_header_name or "",
            "custom_auth_header_present": bool(custom_auth_header_value),
        },
        "endpoint": {
            "base_url": base,
            "host": host,
            "dns_resolves": host_ok,
            "dns_info": host_info,
        },
        "feasible_now": bool(
            has_openai
            and host_ok
            and (
                bool(effective.get("OPENAI_API_KEY"))
                or bool(custom_auth_header_name and custom_auth_header_value)
            )
        ),
    }

    print(json.dumps(report, indent=2))

    if not report["feasible_now"]:
        print(
            "\nResult: NOT immediately feasible in current env.\n"
            "Needed: install dependencies, reachable endpoint DNS/network, and API key."
        )
        return 1

    print("\nResult: Feasible now (minimum prerequisites satisfied).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
