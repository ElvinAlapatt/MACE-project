from typing import TypedDict , Annotated ,List
import operator

class MACEState(TypedDict):
    messages : Annotated[List[str], operator.add]
    code : str
    feedback : str  
    docs : str 
    iteration_count : int 
    current_agent : str 