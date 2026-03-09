from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage , AIMessage
from .state import MACEState
from .prompts import CODER_SYSTEM_PROMPT , QA_SYSTEM_PROMPT , CODER_RETRY_PROMPT
from .utils import extract_code, run_code_safely

# Initialize the model ONCE at module level (not inside the function)
# This avoids re-creating the connection on every single call
coder_llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0.2,       # Low temperature = more deterministic, consistent code
    base_url="http://localhost:11434"  # Default Ollama address
)
qa_llm = ChatOllama(
    model="deepseek-r1:8b",
    temperature=0.1,
    base_url="http://localhost:11434"
)

def coder_node(state: MACEState) -> MACEState:
    """
    The Lead Developer agent.
    
    Reads:  state['user_request']
    Writes: state['generated_code'], state['messages']
    """
    
    print("\n🧑‍💻 [CODER AGENT] Received task:", state["user_request"])
    
    # Build the message list for the LLM
    messages = [
        SystemMessage(content=CODER_SYSTEM_PROMPT),
        HumanMessage(content=f"Write Python code for the following task:\n\n{state['user_request']}")
    ]
    
    # Call the model
    print("🧑‍💻 [CODER AGENT] Generating code...")
    response = coder_llm.invoke(messages)
    
    generated_code = response.content
    
    print("🧑‍💻 [CODER AGENT] Done. Code generated.")
    
    # Return ONLY the fields we're updating
    # LangGraph merges this back into the full state
    return {
        "generated_code": generated_code,
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
    
    # Step 2: Actually RUN the code
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
    qa_response = response.content
    
    # Step 4: Parse STATUS from the response
    qa_status = "fail"  # default to fail (safe default)
    if "STATUS: PASS" in qa_response.upper():
        qa_status = "pass"
    
    print(f"🔍 [QA AGENT] Decision: {qa_status.upper()}")
    if qa_status == "fail":
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
    Knows about its previous failure and QA feedback.
    
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