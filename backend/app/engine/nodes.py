from langchain_ollama import ChatOllama
from .prompts import CODER_PROMPT
from .state import MACEState

#initialising the models
coder_slm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

def coding_node(state : MACEState):

    response = coder_slm.invoke([("system",CODER_PROMPT)] + state["messages"])
    return {
        "code" : response.content,
        "iteration_count" : state["iteration_count"] + 1,
        "messages" : [response.content]
    }

