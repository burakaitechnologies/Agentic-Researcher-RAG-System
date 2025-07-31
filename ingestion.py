import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import tiktoken

load_dotenv()

api_key = os.environ.get("PINECONE_API_KEY")
environment = os.environ.get("PINECONE_ENVIRONMENT")
index_name = os.environ.get("INDEX_NAME", "rag-pinecone")

if not api_key or not environment:
    raise ValueError("PINECONE_API_KEY and PINECONE_ENVIRONMENT must be set in your .env file")

pc = Pinecone(api_key=api_key)

def get_retriever():
    """Get retriever from existing Pinecone index without running ingestion."""
    embeddings = OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )
    # Configure retriever with similarity threshold to avoid irrelevant results
    return vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 4,
            "score_threshold": 0.7  # Only return documents with similarity > 0.7
        }
    )

def run_ingestion():
    """Run the full ingestion process."""
    index_exists = index_name in pc.list_indexes().names()
    
    if not index_exists:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-west-2")
        )
        print(f"Created new index '{index_name}'")
    else:
        index = pc.Index(index_name)
        index.delete(delete_all=True)
        print(f"Cleared all vectors from existing index '{index_name}'")
    
    urls = [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
        "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
    ]
    
    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    total_tokens = sum(len(encoding.encode(doc.page_content)) for doc in docs_list)
    
    print(f"Total number of tokens in docs_list: {total_tokens}")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=200,
        chunk_overlap=20
    )
    
    doc_splits = text_splitter.split_documents(docs_list)
    
    embeddings = OpenAIEmbeddings()
    
    # Get the index reference
    index = pc.Index(index_name)
    
    vectorstore = PineconeVectorStore.from_documents(
        documents=doc_splits,
        embedding=embeddings,
        index_name=index_name
    )
    
    print(f"Pinecone index '{index_name}' created/connected and data loaded.")
    print("Retriever is ready to use.")
    return vectorstore.as_retriever()

embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

# Configure retriever with similarity threshold to avoid irrelevant results
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 4,
        "score_threshold": 0.7  # Only return documents with similarity > 0.7
    }
)
if __name__ == "__main__":
    run_ingestion()
