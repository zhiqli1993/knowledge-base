from __future__ import annotations

import asyncio
import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from fastmcp import Client

MCP_STARTUP_TIMEOUT_SECONDS = 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test a built kb binary bundle.")
    parser.add_argument("bundle_dir", type=Path)
    return parser.parse_args()


def executable_name(base_name: str) -> str:
    return f"{base_name}.exe" if os.name == "nt" else base_name


def choose_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, env=env, check=True, text=True, capture_output=True)


def wait_for_health(url: str, timeout_seconds: float) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(f"{url}/healthz", timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


async def validate_mcp_proxy(mcp_command: str, env: dict[str, str]) -> None:
    client = Client(
        {
            "mcpServers": {
                "knowledge-base": {
                    "command": mcp_command,
                    "env": env,
                }
            }
        },
        # PyInstaller onefile binaries can spend tens of seconds unpacking on
        # first launch, so the MCP handshake needs a longer timeout than the
        # installed-command smoke path.
        timeout=MCP_STARTUP_TIMEOUT_SECONDS,
    )
    async with client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        if "kb_status" not in tool_names:
            raise SystemExit(f"kb-mcp did not expose kb_status. Available tools: {sorted(tool_names)}")
        await client.call_tool("kb_status")


def main() -> int:
    args = parse_args()
    bundle_dir = args.bundle_dir.resolve()
    kb_binary = bundle_dir / executable_name("kb")
    http_binary = bundle_dir / executable_name("kb-http")
    mcp_binary = bundle_dir / executable_name("kb-mcp")

    missing = [str(path) for path in (kb_binary, http_binary, mcp_binary) if not path.exists()]
    if missing:
        raise SystemExit(f"Missing bundled binaries: {', '.join(missing)}")

    workspace = Path(tempfile.mkdtemp(prefix="kb-binary-smoke-"))
    try:
        port = choose_port()
        config_path = workspace / "config.json"
        chroma_dir = workspace / "chroma"
        local_dir = workspace / "local"
        local_dir.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(
                {
                    "chroma": {"persist_directory": str(chroma_dir)},
                    "service": {"host": "127.0.0.1", "port": port, "timeout_seconds": 20},
                    "local": {"allowed_paths": [str(local_dir)]},
                }
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["KNOWLEDGE_BASE_CONFIG"] = str(config_path)

        run([str(kb_binary), "--help"], env)
        run([str(kb_binary), "serve"], env)
        if not wait_for_health(f"http://127.0.0.1:{port}", 20):
            raise SystemExit("kb binary did not start the companion service successfully")
        asyncio.run(validate_mcp_proxy(str(mcp_binary), env))
        run([str(kb_binary), "status"], env)
        run([str(kb_binary), "stop"], env)
        print(f"Binary smoke test passed for {bundle_dir}")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
