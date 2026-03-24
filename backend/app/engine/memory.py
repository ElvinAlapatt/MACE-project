import sqlite3
import os
from datetime import datetime
import re

# Walk up from this file's location to find the project root
# This file is at: backend/app/engine/memory.py
# Project root is: mace-project/
_THIS_FILE = os.path.abspath(__file__)                    # .../backend/app/engine/memory.py
_ENGINE_DIR = os.path.dirname(_THIS_FILE)                 # .../backend/app/engine/
_APP_DIR = os.path.dirname(_ENGINE_DIR)                   # .../backend/app/
_BACKEND_DIR = os.path.dirname(_APP_DIR)                  # .../backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)             # .../mace-project/
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")           # .../mace-project/data/
DB_PATH = os.path.join(_DATA_DIR, "memory.db")            # .../mace-project/data/memory.db

print(f"🧠 [MEMORY] DB path: {DB_PATH}")  # temporary debug line

def init_db():
    """
    Creates the database and tables if they don't exist.
    Called once when MACE starts up.
    
    Two tables:
    - runs:     stores every completed run
    - feedback: stores QA lessons learned
    """
    # Make sure the data/ folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: Full run history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            task        TEXT NOT NULL,
            final_code  TEXT NOT NULL,
            qa_status   TEXT NOT NULL,
            retry_count INTEGER NOT NULL,
            documentation TEXT
        )
    """)

    # Table 2: Lessons learned from QA failures
    # This is what the coder reads before generating
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_memory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            task        TEXT NOT NULL,
            mistake     TEXT NOT NULL,
            frequency   INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()
    print("🧠 [MEMORY] Database initialized.")


def store_run(task: str, final_code: str, qa_status: str,
              retry_count: int, documentation: str, qa_feedback: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO runs (timestamp, task, final_code, qa_status, retry_count, documentation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        task,
        final_code,
        qa_status,
        retry_count,
        documentation
    ))

    # Only store lessons from runs that needed retries
    # AND only if the final qa_feedback is actually a failure message
    # NOT a pass message
    if retry_count > 0 and qa_feedback:
        feedback_upper = qa_feedback.upper()
        # Only store if this is failure feedback, not pass feedback
        if "STATUS: FAIL" in feedback_upper or "STATUS: IMPOSSIBLE" in feedback_upper:
            _store_lesson(cursor, task, qa_feedback)

    conn.commit()
    conn.close()


def _store_lesson(cursor, task: str, qa_feedback: str):
    lesson = qa_feedback

    # Extract just the FEEDBACK text
    if "FEEDBACK:" in qa_feedback.upper():
        lesson = qa_feedback.split("FEEDBACK:")[-1].strip()

    # Remove code blocks
    lesson = re.sub(r"```.*?```", "", lesson, flags=re.DOTALL).strip()

    # Keep only the first two sentences — the core lesson
    # This makes deduplication more effective
    sentences = lesson.replace("\n", " ").split(".")
    lesson = ". ".join(s.strip() for s in sentences[:2] if s.strip()) + "."

    # Clean whitespace
    lesson = " ".join(lesson.split())

    if not lesson or len(lesson) < 10:
        return

    # Fuzzy deduplication — check if a similar lesson exists
    # by looking for significant word overlap
    cursor.execute("SELECT id, mistake, frequency FROM feedback_memory")
    existing_lessons = cursor.fetchall()

    for lesson_id, existing_mistake, freq in existing_lessons:
        # If 60%+ of words overlap, treat as same lesson
        existing_words = set(existing_mistake.lower().split())
        new_words = set(lesson.lower().split())
        if len(existing_words) == 0:
            continue
        overlap = len(existing_words & new_words) / len(existing_words)
        if overlap > 0.6:
            # Same lesson — increment frequency
            cursor.execute("""
                UPDATE feedback_memory
                SET frequency = frequency + 1, timestamp = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), lesson_id))
            return

    # Genuinely new lesson — store it
    cursor.execute("""
        INSERT INTO feedback_memory (timestamp, task, mistake, frequency)
        VALUES (?, ?, ?, 1)
    """, (datetime.now().isoformat(), task, lesson))


def get_relevant_memory(task: str, limit: int = 5) -> str:
    """
    Called by the Coder agent BEFORE generating code.
    Returns the most important lessons learned from past failures.
    
    Prioritizes by frequency — mistakes made more often
    appear at the top so the coder learns from them most.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get top lessons ordered by frequency (most repeated mistakes first)
    cursor.execute("""
        SELECT mistake, frequency
        FROM feedback_memory
        ORDER BY frequency DESC, timestamp DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""

    # Format as a clear warning for the coder
    memory_text = "LESSONS FROM PAST FAILURES (ordered by frequency):\n"
    for i, (mistake, frequency) in enumerate(rows, 1):
        memory_text += f"\n{i}. [Seen {frequency}x] {mistake}"

    return memory_text


def get_run_history(limit: int = 10) -> list:
    """
    Returns the last N runs.
    Used by the FastAPI endpoint in Phase 5.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, task, qa_status, retry_count
        FROM runs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "task": row[2],
            "qa_status": row[3],
            "retry_count": row[4]
        }
        for row in rows
    ]


def get_memory_stats() -> dict:
    """
    Returns stats about what MACE has learned.
    Used by FastAPI in Phase 5.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM runs")
    total_runs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM runs WHERE qa_status = 'pass'")
    passed_runs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback_memory")
    lessons_learned = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(retry_count) FROM runs")
    total_retries = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "failed_runs": total_runs - passed_runs,
        "lessons_learned": lessons_learned,
        "total_retries": total_retries
    }