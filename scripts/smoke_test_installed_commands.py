from __future__ import annotations

import asyncio
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


def choose_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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
        timeout=10,
    )
    async with client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        if "kb_status" not in tool_names:
            raise SystemExit(f"Installed kb-mcp did not expose kb_status. Available tools: {sorted(tool_names)}")
        await client.call_tool("kb_status")


def resolve_command(name: str) -> str:
    command = shutil.which(name)
    if not command:
        raise SystemExit(f"Could not find installed command: {name}")
    return command


def main() -> int:
    kb_command = resolve_command("kb")
    kb_http_command = resolve_command("kb-http")
    kb_mcp_command = resolve_command("kb-mcp")

    workspace = Path(tempfile.mkdtemp(prefix="kb-installed-smoke-"))
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

        subprocess.run([kb_command, "--help"], env=env, check=True, text=True, capture_output=True)
        http_process = subprocess.Popen(
            [kb_http_command],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            if not wait_for_health(f"http://127.0.0.1:{port}", 20):
                raise SystemExit("Installed kb-http command did not become healthy")
            asyncio.run(validate_mcp_proxy(kb_mcp_command, env))
            subprocess.run([kb_command, "status"], env=env, check=True, text=True, capture_output=True)
        finally:
            if http_process.poll() is None:
                http_process.terminate()
                try:
                    http_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    http_process.kill()
                    http_process.wait(timeout=5)
        print("Installed command smoke test passed")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
