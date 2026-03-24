from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .state import MACEState
from .prompts import CODER_SYSTEM_PROMPT, QA_SYSTEM_PROMPT, CODER_RETRY_PROMPT, DOCUMENTARIAN_SYSTEM_PROMPT
from .utils import extract_code, run_code_safely
import re
import os
from dotenv import load_dotenv
from .memory import init_db , store_run , get_relevant_memory

init_db()

load_dotenv()

from langchain_groq import ChatGroq
print("⚡ [MACE] Using Groq cloud models")

coder_llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)
qa_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)
doc_llm = ChatGroq(
    model="llama-3.3-70b-versatile",   # same as QA — good at structured writing
    temperature=0.3,                    # slightly higher = more natural writing
    api_key=os.getenv("GROQ_API_KEY")
)


def parse_qa_response(raw: str) -> str:
    """
    Handles different response formats:
    - Groq models: clean direct response
    - deepseek-r1: answer buried in <think> blocks
    """
    if "</think>" in raw:
        after_think = raw.split("</think>")[-1].strip()
        if after_think:
            return after_think

    inside = re.sub(r"</?think>", "", raw, flags=re.DOTALL).strip()
    if inside:
        return inside

    return raw.strip()


def coder_node(state: MACEState) -> MACEState:
    """
    The Lead Developer agent.
    Now reads past lessons before generating.
    """
    print("\n🧑‍💻 [CODER AGENT] Received task:", state["user_request"])

    # Read memory — what has MACE learned from past failures?
    memory_context = get_relevant_memory(state["user_request"])

    if memory_context:
        print("🧠 [CODER AGENT] Loaded past lessons from memory.")
        user_message = f"""Write Python code for the following task:

TASK:
{state['user_request']}

{memory_context}

Apply these lessons to avoid repeating past mistakes.
"""
    else:
        print("🧠 [CODER AGENT] No past lessons found. Starting fresh.")
        user_message = f"Write Python code for the following task:\n\n{state['user_request']}"

    messages = [
        SystemMessage(content=CODER_SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    print("🧑‍💻 [CODER AGENT] Generating code...")
    response = coder_llm.invoke(messages)
    print("🧑‍💻 [CODER AGENT] Done. Code generated.")

    return {
        "generated_code": response.content,
        "memory_context": memory_context,
        "messages": messages + [response]
    }


def qa_node(state: MACEState) -> MACEState:
    """
    The QA Engineer agent.

    Reads:  state['generated_code'], state['user_request']
    Writes: state['qa_status'], state['qa_feedback'], state['test_results']
    """
    print("\n🔍 [QA AGENT] Starting review...")

    # Step 1: Extract raw code from markdown
    raw_code = extract_code(state["generated_code"])

    # Step 2: Actually RUN the code in sandbox
    print("🔍 [QA AGENT] Executing code in sandbox...")
    execution_result = run_code_safely(raw_code)

    test_summary = f"""
EXECUTION STATUS: {"✅ Success" if execution_result["success"] else "❌ Failed"}
STDOUT: {execution_result["stdout"] or "(none)"}
STDERR: {execution_result["stderr"] or "(none)"}
ERROR TYPE: {execution_result["error_type"] or "(none)"}
    """.strip()

    print(f"🔍 [QA AGENT] Execution result: {'PASS' if execution_result['success'] else 'FAIL'}")

    # Step 3: Ask the QA LLM to analyze
    messages = [
        SystemMessage(content=QA_SYSTEM_PROMPT),
        HumanMessage(content=f"""
ORIGINAL TASK:
{state["user_request"]}

GENERATED CODE:
{raw_code}

EXECUTION RESULTS:
{test_summary}

Provide your STATUS and FEEDBACK.
        """)
    ]

    response = qa_llm.invoke(messages)

    # Step 4: Parse response — handles both Groq and deepseek-r1 formats
    qa_response = parse_qa_response(response.content)

    # Step 5: Parse STATUS — order matters
    qa_status = "fail"
    if qa_response:
        if "STATUS: PASS" in qa_response.upper():
            qa_status = "pass"
        elif "STATUS: IMPOSSIBLE" in qa_response.upper():
            qa_status = "impossible"
    else:
        qa_response = "STATUS: FAIL\nFEEDBACK: QA agent returned empty response. Please retry."
        print("⚠️  [QA AGENT] Warning: Empty response from model")

    print(f"🔍 [QA AGENT] Decision: {qa_status.upper()}")
    if qa_status != "pass":
        print(f"🔍 [QA AGENT] Feedback: {qa_response}")

    # At the end of qa_node, update the return:
    return_data = {
        "qa_status": qa_status,
        "qa_feedback": qa_response,
        "test_results": test_summary,
        "messages": [response]
    }

    # Only store failure feedback — don't overwrite with pass verdicts
    if qa_status in ["fail", "impossible"]:
        return_data["failure_feedback"] = qa_response

    return return_data


def coder_retry_node(state: MACEState) -> MACEState:
    new_retry_count = state["retry_count"] + 1
    print(f"\n🔄 [CODER RETRY] Attempt {new_retry_count} of {state['max_retries']}...")

    memory_context = state.get("memory_context", "")

    content = f"""
ORIGINAL TASK:
{state["user_request"]}

YOUR PREVIOUS CODE:
{state["generated_code"]}

QA FEEDBACK:
{state["qa_feedback"]}
"""
    if memory_context:
        content += f"\n{memory_context}\n"

    content += "\nPlease fix the code addressing all feedback above."

    messages = [
        SystemMessage(content=CODER_RETRY_PROMPT),
        HumanMessage(content=content)
    ]

    response = coder_llm.invoke(messages)
    print(f"🔄 [CODER RETRY] New code generated.")

    return {
        "generated_code": response.content,
        "retry_count": new_retry_count,
        "messages": [response]
    }

def documentarian_node(state: MACEState) -> MACEState:
    """
    The Technical Documentarian agent.
    Only runs after QA has approved the code.

    Reads:  state['generated_code'], state['user_request']
    Writes: state['documentation']
    """
    print("\n📝 [DOCUMENTARIAN] Generating documentation...")

    # Extract clean code — same as QA does
    raw_code = extract_code(state["generated_code"])

    messages = [
        SystemMessage(content=DOCUMENTARIAN_SYSTEM_PROMPT),
        HumanMessage(content=f"""
ORIGINAL TASK:
{state["user_request"]}

APPROVED CODE:
{raw_code}

Generate the markdown documentation for this code.
        """)
    ]

    response = doc_llm.invoke(messages)
    documentation = response.content

    print("📝 [DOCUMENTARIAN] Documentation complete.")

    return {
        "documentation": documentation,
        "messages": [response]
    }

def memory_node(state: MACEState) -> MACEState:
    print("\n🧠 [MEMORY] Storing run and updating lessons...")

    store_run(
        task=state["user_request"],
        final_code=state["generated_code"],
        qa_status=state["qa_status"],
        retry_count=state["retry_count"],
        documentation=state.get("documentation", ""),
        qa_feedback=state.get("failure_feedback", "")  # ← use failure_feedback
    )

    print("🧠 [MEMORY] Done. Memory updated.")
    return {}