from typing import Any, Dict

from graph.state import GraphState
from ingestion import retriever

def retrieve(state: GraphState) -> Dict[str, Any]:
    """
    Retrieves relevant documents based on the question in the current state.

    Args:
        state (GraphState): The current state of the graph, containing the question.

    Returns:
        Dict[str, Any]: A dictionary containing the retrieved documents and the original question.
    """
    print("---RETRIEVE---")
    question = state["question"]

    documents = retriever.invoke(question)

    return {"documents": documents}
