from dotenv import load_dotenv

load_dotenv()

from graph.graph import app

if __name__ == "__main__":
    print("Hello Advanced RAG")
    
    # Ask a question to the RAG system
    question = "How memory works on ai"
    answer = app.invoke(input={"question": question})
    
    # Print the results
    print("---QUESTION---")
    print(answer["question"])
    print("---ANSWER---")
    print(answer["generation"])
    print("---DOCUMENTS---")
    print(answer["documents"])
