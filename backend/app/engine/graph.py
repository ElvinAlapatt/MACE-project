from langgraph.graph import StateGraph, END
from .state import MACEState
from .nodes import coder_node, qa_node, coder_retry_node, documentarian_node


def should_retry_or_end(state: MACEState) -> str:
    if state["qa_status"] == "pass":
        print("\n✅ [ORCHESTRATOR] QA passed. Sending to Documentarian.")
        return "approved"

    if state["qa_status"] == "impossible":
        print(f"\n🚫 [ORCHESTRATOR] Task is impossible. Stopping early.")
        return "impossible"

    if state["retry_count"] >= state["max_retries"]:
        print(f"\n⛔ [ORCHESTRATOR] Max retries ({state['max_retries']}) reached. Stopping.")
        return "max_retries_reached"

    print(f"\n🔁 [ORCHESTRATOR] QA failed. Sending back to Coder. (Attempt {state['retry_count'] + 1}/{state['max_retries']})")
    return "retry"


def build_graph():
    graph = StateGraph(MACEState)

    # Register all nodes
    graph.add_node("coder", coder_node)
    graph.add_node("qa", qa_node)
    graph.add_node("coder_retry", coder_retry_node)
    graph.add_node("documentarian", documentarian_node)  # ← new

    # Entry point
    graph.set_entry_point("coder")

    # Coder always goes to QA
    graph.add_edge("coder", "qa")

    # After retry always goes back to QA
    graph.add_edge("coder_retry", "qa")

    # After documentarian we're done
    graph.add_edge("documentarian", END)             # ← new

    # QA decision
    graph.add_conditional_edges(
        "qa",
        should_retry_or_end,
        {
            "approved": "documentarian",             # ← changed from END
            "retry": "coder_retry",
            "impossible": END,
            "max_retries_reached": END
        }
    )

    return graph.compile()


mace_graph = build_graph()