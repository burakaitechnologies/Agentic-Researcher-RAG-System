from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
import time
from graph.graph import app as rag_app

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    # Don't send any initial message on connect
    pass

@socketio.on('user_message')
def handle_user_message(data):
    message = data.get('message', '')
    print(f"Received message: {message}")
    
    # Start workflow updates
    emit('workflow_update', {'type': 'reset'})
    
    try:
        # Process through RAG system with real-time step tracking
        print("---PROCESSING QUESTION---")
        
        # Track actual execution steps
        executed_steps = []
        
        # Custom callback to track node execution
        def node_callback(node_name):
            executed_steps.append(node_name)
            print(f"---TRACKING STEP: {node_name}---")  # Debug output
            emit('workflow_update', {
                'type': 'node_executed', 
                'node': node_name,
                'executed_steps': executed_steps.copy()
            })
            socketio.sleep(0.5)  # Small delay for visual effect
        
        # Add initial routing step
        node_callback('route_question')
        
        # Stream the execution with callbacks
        final_state = {}
        previous_node = None
        generation_attempts = 0
        
        for step in rag_app.stream({"question": message}):
            node_name = list(step.keys())[0]
            print(f"---EXECUTING NODE: {node_name}---")  # Debug output
            
            # ALWAYS track the actual node execution FIRST
            node_callback(node_name)
            
            # Add decision steps based on workflow logic AFTER the node
            if node_name == 'grade_documents':
                # After grading documents, show the decision step
                node_callback('decide_to_generate')
            elif node_name == 'generate':
                # After generation, check for hallucinations and relevance
                if generation_attempts > 0:
                    # This is a regeneration attempt
                    node_callback('hallucination_check')
                node_callback('grade_generation_relevance')
                generation_attempts += 1
            
            # Accumulate all state data
            final_state.update(step[node_name])
            previous_node = node_name
        
        # Mark workflow as complete
        emit('workflow_update', {'type': 'complete'})
        
        # Send the final answer with resources to chat
        answer = final_state.get('generation', 'No answer generated')
        documents = final_state.get('documents', [])
        
        # Prepare resources data - serialize documents
        serialized_documents = []
        for doc in documents:
            if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                serialized_documents.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
            else:
                # Fallback for other document types
                serialized_documents.append({
                    'content': str(doc),
                    'metadata': {}
                })
        
        # Get web search results if available
        web_results = final_state.get('web_results', [])
        serialized_web_results = []
        
        print(f"---WEB RESULTS COUNT: {len(web_results)}---")  # Debug output
        
        for web_result in web_results:
            if hasattr(web_result, 'page_content') and hasattr(web_result, 'metadata'):
                serialized_web_results.append({
                    'title': web_result.metadata.get('title', 'Web Result'),
                    'snippet': web_result.page_content[:200] + '...' if len(web_result.page_content) > 200 else web_result.page_content,
                    'url': web_result.metadata.get('source', '#')
                })
            elif isinstance(web_result, dict):
                serialized_web_results.append({
                    'title': web_result.get('title', 'Web Result'),
                    'snippet': web_result.get('snippet', web_result.get('content', 'No preview available')),
                    'url': web_result.get('url', web_result.get('source', '#'))
                })
        
        resources = {
            'documents': serialized_documents,
            'web_results': serialized_web_results
        }
        
        emit('ai_response', {'message': answer, 'resources': resources})
        
        print("---QUESTION---")
        print(final_state.get('question', message))
        print("---ANSWER---")
        print(answer)
        print("---DOCUMENTS---")
        print(documents)
        
    except Exception as e:
        print(f"Error processing question: {e}")
        emit('ai_response', {'message': f"Sorry, I encountered an error processing your question: {str(e)}"})
        emit('workflow_update', {'type': 'error'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5001)