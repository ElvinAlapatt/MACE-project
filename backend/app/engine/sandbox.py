"""
sandbox.py — Isolated code execution for the QA agent.

Primary path: run untrusted code in a throwaway Docker container with
  - no network access
  - hard memory limit
  - hard CPU limit
  - PID limit (fork-bomb protection)
  - read-only root filesystem (only /tmp is writable, and it's tmpfs-capped)
  - non-root user

Fallback path: if no Docker daemon is reachable (e.g. on a Render web
service without a docker socket), we fall back to the existing
subprocess-based execution so the QA loop keeps working in production.
The fallback is logged loudly so it shows up in your demo/metrics —
this is intentional, not silent degradation.

Usage from utils.py:

    from app.engine.sandbox import run_code_in_docker, docker_is_available

    result = run_code_in_docker(code)
    if result is None:
        result = run_code_with_subprocess(code)   # your existing function
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, TypedDict

logger = logging.getLogger("mace.sandbox")

try:
    import docker
    from docker.errors import DockerException
    _DOCKER_SDK_INSTALLED = True
except ImportError:
    _DOCKER_SDK_INSTALLED = False

SANDBOX_IMAGE = "mace-sandbox:latest"
CONTAINER_TIMEOUT_SECONDS = 10
MEMORY_LIMIT = "128m"
CPU_PERIOD = 100_000
CPU_QUOTA = 50_000          # 0.5 CPU
PIDS_LIMIT = 64
TMPFS_SIZE = "16m"

_client = None
_availability_checked = False
_available = False


class SandboxResult(TypedDict):
    success: bool
    stdout: str
    stderr: str
    exit_code: Optional[int]
    timed_out: bool
    backend: str  # "docker" or "subprocess" — useful for your /api/metrics endpoint


def docker_is_available() -> bool:
    """Cached check — only pings the daemon once per process lifetime."""
    global _client, _availability_checked, _available

    if _availability_checked:
        return _available

    _availability_checked = True

    if not _DOCKER_SDK_INSTALLED:
        logger.warning(
            "docker SDK not installed (pip install docker) — sandbox will use subprocess fallback."
        )
        _available = False
        return _available

    try:
        _client = docker.from_env()
        _client.ping()
        _available = True
        logger.info("Docker daemon reachable — using isolated container sandbox.")
    except Exception as e:  # docker.errors.DockerException, ConnectionError, etc.
        logger.warning(
            f"Docker daemon not reachable ({e}) — falling back to subprocess sandbox. "
            "This is expected on Render web services without a docker socket."
        )
        _client = None
        _available = False

    return _available


def run_code_in_docker(code: str, language: str = "python") -> Optional[SandboxResult]:
    """
    Attempts isolated execution in Docker.
    Returns None (not a failure result) if Docker isn't available at all,
    so the caller knows to fall back to subprocess — vs. a real SandboxResult
    with success=False when the *code itself* failed inside the container.
    """
    if not docker_is_available():
        return None

    if language == "python":
        ext, run_cmd = "py", ["python3", "/sandbox/code.py"]
    elif language == "javascript":
        ext, run_cmd = "js", ["node", "/sandbox/code.js"]
    else:
        raise ValueError(f"Unsupported language for sandbox: {language}")

    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = Path(tmpdir) / f"code.{ext}"
        code_path.write_text(code, encoding="utf-8")

        container = None
        try:
            container = _client.containers.run(
                image=SANDBOX_IMAGE,
                command=run_cmd,
                volumes={tmpdir: {"bind": "/sandbox", "mode": "ro"}},
                working_dir="/sandbox",
                network_disabled=True,
                mem_limit=MEMORY_LIMIT,
                memswap_limit=MEMORY_LIMIT,  # prevents swap from masking the mem limit
                cpu_period=CPU_PERIOD,
                cpu_quota=CPU_QUOTA,
                pids_limit=PIDS_LIMIT,
                read_only=True,
                tmpfs={"/tmp": f"size={TMPFS_SIZE}"},
                detach=True,
            )

            try:
                wait_result = container.wait(timeout=CONTAINER_TIMEOUT_SECONDS)
                exit_code = wait_result.get("StatusCode", 1)
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
                return SandboxResult(
                    success=(exit_code == 0),
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    timed_out=False,
                    backend="docker",
                )
            except Exception:
                # container.wait() raises on timeout (requests.exceptions.ReadTimeout
                # under the hood) — treat any wait failure here as a timeout.
                try:
                    container.kill()
                except Exception:
                    pass
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution exceeded {CONTAINER_TIMEOUT_SECONDS}s timeout",
                    exit_code=None,
                    timed_out=True,
                    backend="docker",
                )
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass