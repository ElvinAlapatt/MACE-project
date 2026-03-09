# backend/app/engine/graph.py

from langgraph.graph import StateGraph, END
from .state import MACEState
from .nodes import coder_node , qa_node , coder_retry_node


def should_retry_or_end(state: MACEState) -> str:
    """
    The brain of the loop. Called after every QA run.
    Returns a string that tells LangGraph which edge to follow.
    
    This is a CONDITIONAL EDGE FUNCTION.
    It must return one of the keys defined in add_conditional_edges below.
    """
    if state["qa_status"] == "pass":
        print("\n✅ [ORCHESTRATOR] QA passed. Moving to END.")
        return "approved"
    
    if state["retry_count"] >= state["max_retries"]:
        print(f"\n⛔ [ORCHESTRATOR] Max retries ({state['max_retries']}) reached. Stopping.")
        return "max_retries_reached"
    
    print(f"\n🔁 [ORCHESTRATOR] QA failed. Sending back to Coder. (Attempt {state['retry_count'] + 1}/{state['max_retries']})")
    return "retry"



def build_graph():
    """
    Constructs the MACE agent graph.
    
    Phase 1: Just the Coder node.
    Phase 2: We'll add QA + conditional loops here.
    """
    
    # Create the graph, telling it what state structure to use
    graph = StateGraph(MACEState)
    
    # Register our node
    graph.add_node("coder", coder_node)
    
    # Set the entry point — where execution begins
    graph.set_entry_point("coder")
    graph.add_node("qa", qa_node)
    graph.add_node("coder_retry", coder_retry_node)
    
    # For now, after coder runs, we're done
    graph.add_edge("coder", END)
    graph.add_edge("coder", "qa")
    graph.add_edge("coder_retry", "qa")


    graph.add_conditional_edges(
        "qa",                       # After this node...
        should_retry_or_end,        # ...call this function to decide...
        {
            "approved": END,                    # ...go here if "approved"
            "retry": "coder_retry",             # ...go here if "retry"
            "max_retries_reached": END          # ...go here if exhausted
        }
    )

    
    # Compile into a runnable
    return graph.compile()


# Create a single instance to be imported elsewhere
mace_graph = build_graph()