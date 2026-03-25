from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.engine.graph import mace_graph
from app.engine.memory import get_run_history, get_memory_stats, get_relevant_memory
import time

from .utils.helpers import extract_clean_code , extract_clean_documentation , extract_clean_feedback 

app = FastAPI(
    title="MACE API",
    description="Multi-Agent Collaborative Environment",
    version="1.0.0"
)

# CORS — allows your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ───────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    task: str
    max_retries: int = 3      # optional, defaults to 3


class GenerateResponse(BaseModel):
    status: str
    retry_count: int
    generated_code: str
    documentation: str
    qa_feedback: str
    time_taken: float


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    """Simple health check — used by Render to verify the service is up."""
    return {"status": "ok", "service": "MACE"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty")

    start_time = time.time()

    try:
        result = mace_graph.invoke({
            "user_request": request.task,
            "generated_code": "",
            "messages": [],
            "qa_feedback": "",
            "qa_status": "",
            "test_results": "",
            "retry_count": 0,
            "max_retries": request.max_retries,
            "documentation": "",
            "memory_context": "",
            "failure_feedback": ""
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MACE pipeline failed: {str(e)}")

    time_taken = round(time.time() - start_time, 2)

    return GenerateResponse(
        status=result.get("qa_status", "unknown"),
        retry_count=result.get("retry_count", 0),
        generated_code=extract_clean_code(result.get("generated_code", "")),
        documentation=extract_clean_documentation(result.get("documentation", "")),
        qa_feedback=extract_clean_feedback(result.get("qa_feedback", "")),
        time_taken=time_taken
    )


@app.get("/api/history")
def history(limit: int = 10):
    """Returns the last N runs from the database."""
    try:
        runs = get_run_history(limit=limit)
        return {"runs": runs, "count": len(runs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory")
def memory():
    """Returns what MACE has learned — stats + lessons."""
    try:
        stats = get_memory_stats()
        lessons = get_relevant_memory("", limit=10)
        return {
            "stats": stats,
            "lessons": lessons
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))