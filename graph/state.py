from typing import List, TypedDict, Annotated
from operator import add

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: The user's question as a string.
        generation: The LLM (Large Language Model) generated response as a string.
        web_search: A boolean indicating whether to perform a web search.
        documents: A list of documents that can be updated by multiple nodes.
        web_results: A list of web search results with metadata.
    """
    question: str
    generation: str
    web_search: bool
    documents: Annotated[List, add]
    web_results: Annotated[List, add]
