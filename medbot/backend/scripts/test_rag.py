import sys
import os

# Adjust path to import app modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.rag import MedicalRAGPipeline

def test_rag_standalone():
    print("=" * 60)
    print("MEDBOT RAG STANDALONE TEST")
    print("=" * 60)
    
    try:
        pipeline = MedicalRAGPipeline()
    except Exception as e:
        print(f"ERROR: Failed to initialize RAG pipeline: {str(e)}")
        sys.exit(1)
        
    # We will test two queries: one that is out-of-scope, and one that is in-scope
    queries = [
        "What is diabetes?",
        "What is Node.js and how do I write a web server?"
    ]
    
    for idx, query in enumerate(queries):
        print("\n" + "-" * 50)
        print(f"QUERY {idx + 1}: '{query}'")
        print("-" * 50)
        
        # 1. Retrieve matches first for logging
        print("Retrieving context from Pinecone...")
        matches = pipeline.retrieve(query)
        if not matches:
            print("No matching contexts retrieved.")
        else:
            print(f"Retrieved {len(matches)} contexts:")
            for match in matches:
                page = match.get("metadata", {}).get("page_number", "Unknown")
                score = match.get("score", 0.0)
                text_snippet = match.get("metadata", {}).get("text", "")[:120].replace('\n', ' ')
                print(f"  - [Page {page}] (Score: {score:.3f}): {text_snippet}...")
                
        # 2. Run Generation (Streaming)
        print("\nStreaming response from LLM:")
        stream, sources = pipeline.generate_response(query, stream=True)
        
        print("ANSWER: ", end="", flush=True)
        for token in stream:
            print(token, end="", flush=True)
        print("\n")
        
        if sources:
            print("SOURCES LOGGED:")
            for src in sources:
                print(f"  - Page {src['page_number']} (Score: {src['score']:.3f})")
        else:
            print("SOURCES LOGGED: None (Hallucination guard triggered)")
            
    print("\n" + "=" * 60)
    print("[OK] RAG Standalone testing script complete.")
    print("=" * 60)

if __name__ == "__main__":
    test_rag_standalone()
