import re
import subprocess
import tempfile
import os
import logging
from typing import Optional

from .sandbox import run_code_in_docker
logger = logging.getLogger("mace.utils")


def extract_code(llm_response: str) -> str:
    """
        pulls raw python code out of a markdown 
    """

    pattern = r"```python\s*(.*?)\s*```"
    match = re.search(pattern, llm_response, re.DOTALL)

    if match:
        return match.group(1).strip()

    pattern = r"```\s*(.*?)\s*```"
    match = re.search(pattern, llm_response, re.DOTALL)

    if match:
        return match.group(1).strip()

    return llm_response.strip()


def run_code_safely(code: str) -> dict:
    """
        Executes the code in an isolated environment.

        Tries the Docker sandbox first (no network, memory/CPU/pid limits,
        non-root, read-only filesystem). If no Docker daemon is reachable
        (e.g. deployed on Render without a docker socket), falls back to
        the subprocess-based execution below so the QA loop never breaks.

        this is how QA truly validates - not by reading,
        but by running

        returns a dict:
        {
            "success": True/False,
            "stdout": "any print message",
            "stderr": "any error message",
            "error_type": "SyntaxError" / None,
            "backend": "docker" / "subprocess"
        }
    """

    docker_result = run_code_in_docker(code)

    if docker_result is not None:
        return {
            "success": docker_result["success"],
            "stdout": docker_result["stdout"],
            "stderr": docker_result["stderr"],
            "error_type": (
                "TimeoutError" if docker_result["timed_out"]
                else _extract_error_type(docker_result["stderr"])
            ),
            "backend": "docker",
        }

    logger.info("Docker sandbox unavailable for this run — using subprocess fallback.")
    return _run_code_subprocess(code)


def _run_code_subprocess(code: str) -> dict:
    """
        Fallback execution path: runs code in a plain subprocess.
        Used automatically when Docker isn't reachable. Kept as its own
        function (rather than inlined) so it stays unit-testable on its
        own, same as before.
    """

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error_type": _extract_error_type(result.stderr),
            "backend": "subprocess",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Code execution timed out after 10 seconds.",
            "error_type": "TimeoutError",
            "backend": "subprocess",
        }
    finally:
        os.unlink(temp_path)


def _extract_error_type(stderr: str) -> Optional[str]:
    if not stderr:
        return None

    lines = stderr.strip().split("\n")
    last_line = lines[-1]
    if ':' in last_line:
        return last_line.split(':')[0].strip()
    return None