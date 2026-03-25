import re

def extract_clean_code(raw: str) -> str:
    """Extracts only the code from markdown code block, strips trailing comments."""
    pattern = r"```python\s*(.*?)\s*```"
    match = re.search(pattern, raw, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        pattern = r"```\s*(.*?)\s*```"
        match = re.search(pattern, raw, re.DOTALL)
        code = match.group(1).strip() if match else raw.strip()

    # Remove trailing commented-out blocks
    lines = code.split("\n")
    cleaned = []
    for line in lines:
        # Stop at commented-out if __name__ blocks
        if line.strip().startswith("# if __name__"):
            break
        cleaned.append(line)

    # Strip trailing comment-only lines from the bottom
    while cleaned and cleaned[-1].strip().startswith("#"):
        cleaned.pop()

    return "\n".join(cleaned).strip()


def extract_clean_feedback(raw: str) -> str:
    """Strips think blocks and extracts only the FEEDBACK text."""
    # Remove think blocks
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    
    # Extract just the FEEDBACK part
    if "FEEDBACK:" in cleaned.upper():
        cleaned = cleaned.split("FEEDBACK:")[-1].strip()
    
    # Remove STATUS line if it's still there
    lines = cleaned.split("\n")
    lines = [l for l in lines if not l.strip().upper().startswith("STATUS:")]
    
    return "\n".join(lines).strip()


def extract_clean_documentation(raw: str) -> str:
    """Strips think blocks, returns clean markdown documentation."""
    # Remove think blocks
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    
    # If it starts with a markdown header it's already clean
    if cleaned.startswith("#"):
        return cleaned
    
    # Try to find where the markdown starts
    lines = cleaned.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            return "\n".join(lines[i:]).strip()
    
    return cleaned.strip()