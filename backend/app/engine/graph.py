from typing_extensions import TypedDict
from langgraph.graph import StateGraph,START,END
from IPython.display import Image, display

from app.engine import nodes

class State(TypedDict):
    graph_state : str 

builder = StateGraph(State)
builder.add_node("node_1",nodes.node1)
builder.add_node("node_2",nodes.node2)
builder.add_node("node_3",nodes.node3)

#workflow

def build_graph():
    builder.add_edge(START,"node_1")
    builder.add_conditional_edges("node_1",nodes.decision_mood)
    builder.add_edge("node_2",END)
    builder.add_edge("node_3",END)
    
    return builder.compile()
    
graph = build_graph()

# png_bytes = graph.get_graph().draw_mermaid_png()
# with open("graph.png", "wb") as f:
#     f.write(png_bytes)
# print("Graph saved as graph.png")

result = graph.invoke({"graph_state" : "Hi, this is Lance."})
print(result)