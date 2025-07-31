from typing import Any, Dict

from langchain.schema import Document
from langchain_tavily import TavilySearch

from graph.state import GraphState
from dotenv import load_dotenv

load_dotenv()
web_search_tool = TavilySearch(max_results=3)


def web_search(state: GraphState) -> Dict[str, Any]:
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents", [])
    web_results = state.get("web_results", [])

    # Get search results from Tavily
    tavily_results = web_search_tool.invoke({"query": question})['results']
    
    # Store web results with metadata for frontend display
    for tavily_result in tavily_results:
        web_doc = Document(
            page_content=tavily_result["content"],
            metadata={
                "title": tavily_result.get("title", "Web Result"),
                "source": tavily_result.get("url", "#"),
                "type": "web_search"
            }
        )
        web_results.append(web_doc)
    
    # Join all search results into one text for RAG processing
    joined_tavily_result = "\n".join(
        [tavily_result["content"] for tavily_result in tavily_results]
    )
    
    # Create a document from search results for RAG
    web_results_doc = Document(page_content=joined_tavily_result)
    documents.append(web_results_doc)
    
    return {"documents": documents, "web_results": web_results}
