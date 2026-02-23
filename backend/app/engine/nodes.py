import random
from typing import Literal

def node1(state):
    return({"graph_state":state['graph_state'] + "I am"})

def node2(state):
    return({"graph_state":state['graph_state'] + " Happy"})

def node3(state):
    return({"graph_state":state['graph_state'] + " Sad"})

def decision_mood(state) -> Literal["node_2","node_3"]:
    if random.random() < 0.5:
        return "node_2"
    return "node_3"
