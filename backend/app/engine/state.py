from typing import Annotated , TypedDict
import operator

class MACEState(TypedDict):
    user_request : str
    generated_code : str
    messages : Annotated[list,operator.add]

    qa_feedback : str
    qa_status : str
    retry_count : int
    max_retries : int
    test_results : str

    documentation: str 
