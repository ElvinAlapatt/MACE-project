from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .state import MACEState
from .prompts import CODER_SYSTEM_PROMPT, QA_SYSTEM_PROMPT, CODER_RETRY_PROMPT, DOCUMENTARIAN_SYSTEM_PROMPT
from .utils import extract_code, run_code_safely
import re
import os
from dotenv import load_dotenv

load_dotenv()

USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

if USE_GROQ:
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
else:
    print("🖥️  [MACE] Using local Ollama models")

    coder_llm = ChatOllama(
        model="qwen2.5-coder:7b",
        temperature=0.2,
        num_ctx=2048,
        num_gpu=20,
        base_url="http://localhost:11434"
    )
    qa_llm = ChatOllama(
        model="deepseek-r1:8b",
        temperature=0.1,
        num_ctx=2048,
        num_gpu=20,
        base_url="http://localhost:11434"
    )
    doc_llm = ChatOllama(
        model="qwen2.5-coder:7b",          # reuse coder model locally
        temperature=0.3,
        num_ctx=2048,
        num_gpu=20,
        base_url="http://localhost:11434"
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

    Reads:  state['user_request']
    Writes: state['generated_code'], state['messages']
    """
    print("\n🧑‍💻 [CODER AGENT] Received task:", state["user_request"])

    messages = [
        SystemMessage(content=CODER_SYSTEM_PROMPT),
        HumanMessage(content=f"Write Python code for the following task:\n\n{state['user_request']}")
    ]

    print("🧑‍💻 [CODER AGENT] Generating code...")
    response = coder_llm.invoke(messages)

    print("🧑‍💻 [CODER AGENT] Done. Code generated.")

    return {
        "generated_code": response.content,
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

    return {
        "qa_status": qa_status,
        "qa_feedback": qa_response,
        "test_results": test_summary,
        "messages": [response]
    }


def coder_retry_node(state: MACEState) -> MACEState:
    """
    The Coder agent in retry mode.

    Reads:  state['user_request'], state['generated_code'],
            state['qa_feedback'], state['retry_count']
    Writes: state['generated_code'], state['retry_count']
    """
    new_retry_count = state["retry_count"] + 1
    print(f"\n🔄 [CODER RETRY] Attempt {new_retry_count} of {state['max_retries']}...")

    messages = [
        SystemMessage(content=CODER_RETRY_PROMPT),
        HumanMessage(content=f"""
ORIGINAL TASK:
{state["user_request"]}

YOUR PREVIOUS CODE:
{state["generated_code"]}

QA FEEDBACK:
{state["qa_feedback"]}

Please fix the code based on this feedback.
        """)
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