import re
import subprocess
import tempfile
import os
from typing import Optional

def extract_code(llm_response : str) -> str:
    """
        pulls raw python code out of a markdown 
    """

    pattern = r"```python\s*(.*?)\s*```"
    match = re.search(pattern, llm_response, re.DOTALL)

    if match:
        return match.group(1).strip()
    
    pattern = r"```\s*(.*?)\s*```"
    match = re.search(pattern,llm_response,re.DOTALL)

    if match:
        return match.group(1).strip()
    
    return llm_response.strip()


def run_code_safely(code : str) -> dict:
    """
        actually executes  the  code in an isolated subprocess

        this is how QA truly validates - not by reading,
        but by running

        returns a dict:
        {
            "success":True/False,
            "stdout":"any print message",
            "stderr":"any error message:,
            "error_type":"SyntaxError" / None
        }
    """

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False  
    ) as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python",temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error_type": _extract_error_type(result.stderr)
        }
    except subprocess.TimeoutExpired:
        return {
            "success" : False,
            "stdout":"",
            "stderr":"Code execution timed out after 10 seconds.",
            "error_type": "TimeoutError"
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