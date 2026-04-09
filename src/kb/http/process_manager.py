import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple
from urllib.request import urlopen

from kb.config import Config, resolve_config_path


def load_config() -> Config:
    return Config.load_from_file(resolve_config_path(os.getenv("KNOWLEDGE_BASE_CONFIG")))


def state_paths(config: Config) -> Tuple[Path, Path, Path]:
    root = Path('~/.kb').expanduser()
    run_dir = root / 'run'
    log_dir = root / 'logs'
    run_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    suffix = str(config.service.port)
    return (
        run_dir / f'service-{suffix}.pid',
        run_dir / f'service-{suffix}.state',
        log_dir / f'service-{suffix}.log',
    )


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _healthcheck(url: str, timeout: float = 1.0) -> bool:
    try:
        with urlopen(f"{url}/healthz", timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def serve() -> str:
    config = load_config()
    pid_path, state_path, log_path = state_paths(config)
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
        except ValueError:
            pid = 0
        if pid and _is_pid_running(pid) and _healthcheck(config.service.local_url):
            return f"KB service already running at {config.service.local_url} (pid {pid})"
        pid_path.unlink(missing_ok=True)
        state_path.unlink(missing_ok=True)

    with open(log_path, 'a', encoding='utf-8') as log_file:
        process = subprocess.Popen(
            [sys.executable, '-m', 'kb.http'],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
            cwd=str(Path.cwd()),
            env=os.environ.copy(),
        )
    pid_path.write_text(str(process.pid), encoding='utf-8')
    state_path.write_text(config.service.local_url, encoding='utf-8')

    deadline = time.time() + config.service.timeout_seconds
    while time.time() < deadline:
        if _healthcheck(config.service.local_url):
            return f"KB service started at {config.service.local_url} (pid {process.pid})"
        time.sleep(0.5)
    return f"KB service started with pid {process.pid}, but health check timed out"


def stop() -> str:
    config = load_config()
    pid_path, state_path, _ = state_paths(config)
    if not pid_path.exists():
        return 'KB service is not running'
    try:
        pid = int(pid_path.read_text().strip())
    except ValueError:
        pid = 0
    if not pid or not _is_pid_running(pid):
        pid_path.unlink(missing_ok=True)
        state_path.unlink(missing_ok=True)
        return 'KB service is not running'
    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + 5
    while time.time() < deadline:
        if not _is_pid_running(pid):
            pid_path.unlink(missing_ok=True)
            state_path.unlink(missing_ok=True)
            return f'KB service stopped (pid {pid})'
        time.sleep(0.25)
    os.kill(pid, signal.SIGKILL)
    pid_path.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    return f'KB service force stopped (pid {pid})'


def restart() -> str:
    stop_msg = stop()
    start_msg = serve()
    return f"{stop_msg}\n{start_msg}"


def read_logs(lines: int = 50) -> str:
    config = load_config()
    _, _, log_path = state_paths(config)
    if not log_path.exists():
        return 'No KB service log file found'
    content = log_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    tail = content[-lines:]
    return '\n'.join(tail) if tail else 'KB service log is empty'
