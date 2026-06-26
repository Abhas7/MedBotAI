import time
import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.config import Config
from fastembed import TextEmbedding
from langchain_ollama import ChatOllama
from pinecone import Pinecone

def run_benchmark():
    print("=== STARTING MEDBOT PERFORMANCE BENCHMARK (FASTEMBED + OLLAMA) ===")
    
    # 1. Initialize Clients
    start_time = time.time()
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)
    index = pc.Index(Config.PINECONE_INDEX_NAME)
    
    # Initialize local fastembed client
    embeddings = TextEmbedding(model_name="nomic-ai/nomic-embed-text-v1.5")
    
    llm = ChatOllama(
        model=Config.LLM_MODEL,
        base_url=Config.OLLAMA_BASE_URL,
        temperature=0.2,
        num_ctx=2048,
        num_predict=Config.LLM_NUM_PREDICT,
        num_thread=Config.LLM_NUM_THREAD
    )
    init_time = time.time() - start_time
    print(f"[*] Clients initialized in {init_time:.2f}s")

    # 2. Benchmark Embedding Generation
    query = "What are the common symptoms of diabetes?"
    print(f"\n[*] Step 1: Generating embedding via local fastembed (Run 1)...")
    start_time = time.time()
    try:
        embeddings_generator = embeddings.embed([query])
        query_vector = [float(x) for x in list(embeddings_generator)[0]]
        print(f"[+] Run 1 completed in {time.time() - start_time:.4f}s (vector length: {len(query_vector)})")
    except Exception as e:
        print(f"[-] Run 1 failed: {e}")
        query_vector = None

    print(f"[*] Generating embedding via local fastembed (Run 2)...")
    start_time = time.time()
    try:
        embeddings_generator = embeddings.embed([query])
        query_vector = [float(x) for x in list(embeddings_generator)[0]]
        print(f"[+] Run 2 completed in {time.time() - start_time:.4f}s")
    except Exception as e:
        print(f"[-] Run 2 failed: {e}")

    print(f"[*] Generating embedding via local fastembed (Run 3)...")
    start_time = time.time()
    try:
        embeddings_generator = embeddings.embed([query])
        query_vector = [float(x) for x in list(embeddings_generator)[0]]
        print(f"[+] Run 3 completed in {time.time() - start_time:.4f}s")
    except Exception as e:
        print(f"[-] Run 3 failed: {e}")

    # 3. Benchmark Pinecone Query
    print("\n[*] Step 2: Querying Pinecone index (Run 1)...")
    start_time = time.time()
    try:
        results = index.query(
            vector=query_vector,
            top_k=1,
            include_metadata=True
        )
        print(f"[+] Run 1 completed in {time.time() - start_time:.2f}s")
        matches = results.get("matches", [])
    except Exception as e:
        print(f"[-] Run 1 failed: {e}")
        matches = []

    print("[*] Querying Pinecone index (Run 2)...")
    start_time = time.time()
    try:
        results = index.query(
            vector=query_vector,
            top_k=2,
            include_metadata=True
        )
        print(f"[+] Run 2 completed in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"[-] Run 2 failed: {e}")

    print("[*] Querying Pinecone index (Run 3)...")
    start_time = time.time()
    try:
        results = index.query(
            vector=query_vector,
            top_k=2,
            include_metadata=True
        )
        print(f"[+] Run 3 completed in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"[-] Run 3 failed: {e}")

    # 4. Benchmark LLM Pre-fill & First Token Latency (Streaming)
    print("\n[*] Step 3: Prompting LLM (Streaming mode for speed)...")
    context_excerpts = []
    for match in matches:
        metadata = match.get("metadata", {})
        text = metadata.get("text", "")
        page_num = metadata.get("page_number", "Unknown")
        score = match.get("score", 0.0)
        context_excerpts.append(f"[Page {page_num}] (Score: {score:.3f}):\n{text}")
    
    context_text = "\n\n".join(context_excerpts)
    system_prompt = (
        "You are MedBot, an expert AI medical assistant trained on medical encyclopedias.\n"
        "Your task is to answer the user's question based ONLY on the provided context excerpts.\n"
        "If the context does not contain enough information to answer the question, respond with: 'I don't know.'\n\n"
        f"Context excerpts:\n{context_text}"
    )
    
    messages = [
        ("system", system_prompt),
        ("human", query)
    ]
    
    start_time = time.time()
    first_token_time = None
    total_tokens = 0
    
    try:
        stream = llm.stream(messages)
        print("[+] Stream opened, receiving tokens: ", end="", flush=True)
        for chunk in stream:
            if chunk.content:
                if first_token_time is None:
                    first_token_time = time.time() - start_time
                print(chunk.content, end="", flush=True)
                total_tokens += 1
        print() # New line after stream
        total_time = time.time() - start_time
        
        if first_token_time:
            generation_time = total_time - first_token_time
            tps = total_tokens / generation_time if generation_time > 0 else 0
            print(f"\n[+] Time to first token (TTFT): {first_token_time:.2f}s")
            print(f"[+] Total generation time: {generation_time:.2f}s for {total_tokens} tokens")
            print(f"[+] Generation speed: {tps:.2f} tokens/second")
            print(f"[+] Total request roundtrip: {total_time:.2f}s")
        else:
            print("[-] No tokens were generated.")
    except Exception as e:
        print(f"\n[-] LLM generation failed: {e}")

if __name__ == "__main__":
    run_benchmark()
