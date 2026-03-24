from langgraph.graph import StateGraph, END
from .state import MACEState
from .nodes import coder_node, qa_node, coder_retry_node, documentarian_node, memory_node

def should_retry_or_end(state: MACEState) -> str:
    if state["qa_status"] == "pass":
        print("\n✅ [ORCHESTRATOR] QA passed. Sending to Documentarian.")
        return "approved"

    if state["qa_status"] == "impossible":
        print(f"\n🚫 [ORCHESTRATOR] Task is impossible. Stopping early.")
        return "impossible"

    if state["retry_count"] >= state["max_retries"]:
        print(f"\n⛔ [ORCHESTRATOR] Max retries reached. Stopping.")
        return "max_retries_reached"

    print(f"\n🔁 [ORCHESTRATOR] QA failed. Sending back to Coder.")
    return "retry"


def build_graph():
    graph = StateGraph(MACEState)

    graph.add_node("coder", coder_node)
    graph.add_node("qa", qa_node)
    graph.add_node("coder_retry", coder_retry_node)
    graph.add_node("documentarian", documentarian_node)
    graph.add_node("memory", memory_node)          # ← new

    graph.set_entry_point("coder")

    graph.add_edge("coder", "qa")
    graph.add_edge("coder_retry", "qa")
    graph.add_edge("documentarian", "memory")      # ← changed from END
    graph.add_edge("memory", END)                  # ← new

    graph.add_conditional_edges(
    "qa",
    should_retry_or_end,
    {
        "approved": "documentarian",
        "retry": "coder_retry",
        "impossible": "memory",         # ← must go to memory
        "max_retries_reached": "memory"  # ← must go to memory
    }
)

    return graph.compile()


mace_graph = build_graph()