import os
import sys
from tqdm import tqdm
import fitz  # PyMuPDF

# Add backend to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings

def run_ingestion():
    print("=" * 60)
    print("MEDBOT PDF INGESTION PIPELINE (OLLAMA)")
    print("=" * 60)
    
    # 1. Validate Config
    missing = Config.validate()
    if missing:
        print(f"ERROR: Missing configuration variables: {', '.join(missing)}")
        print("Please check your backend/.env configuration before running this script.")
        sys.exit(1)
        
    # 2. Check PDF location
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(backend_dir, "data", "gale_encyclopedia.pdf")
    
    # Ensure data folder exists
    data_dir = os.path.dirname(pdf_path)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at: {pdf_path}")
        print("Please create the 'data' directory and place the 'gale_encyclopedia.pdf' inside it.")
        sys.exit(1)
        
    print(f"[OK] Found PDF file: {pdf_path}")
    
    # 3. Setup Pinecone Client
    try:
        print("Initializing Pinecone connection...")
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        
        # Check if index exists, create it if it doesn't
        active_indexes = [idx.name for idx in pc.list_indexes()]
        if Config.PINECONE_INDEX_NAME not in active_indexes:
            print(f"Index '{Config.PINECONE_INDEX_NAME}' not found in Pinecone. Creating serverless index...")
            pc.create_index(
                name=Config.PINECONE_INDEX_NAME,
                dimension=768,  # dimension for nomic-embed-text
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"[OK] Index '{Config.PINECONE_INDEX_NAME}' created successfully.")
        else:
            print(f"[OK] Connected to Pinecone index: '{Config.PINECONE_INDEX_NAME}'")
            # Verify index dimension matches Ollama embeddings
            index_desc = pc.describe_index(Config.PINECONE_INDEX_NAME)
            if index_desc.dimension != 768:
                print(f"WARNING: Pinecone index dimension is {index_desc.dimension}, but Ollama nomic-embed-text requires 768.")
                print("If you get dimension errors, please delete and recreate your Pinecone index with 768 dimensions.")
            
        index = pc.Index(Config.PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"ERROR: Failed to connect to Pinecone: {str(e)}")
        sys.exit(1)
        
    # 4. Initialize Ollama Embeddings Client
    try:
        print(f"Initializing Ollama Embeddings client (Model: {Config.EMBEDDING_MODEL})...")
        embeddings = OllamaEmbeddings(
            model=Config.EMBEDDING_MODEL,
            base_url=Config.OLLAMA_BASE_URL
        )
        print("[OK] Ollama Embeddings client initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Ollama Embeddings: {str(e)}")
        sys.exit(1)
        
    # 5. Extract and Chunk PDF Content
    print("Reading and parsing PDF pages...")
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Loaded PDF containing {total_pages} pages.")
    except Exception as e:
        print(f"ERROR: Failed to open PDF file: {str(e)}")
        sys.exit(1)
        
    # Setup token splitter (tiktoken cl100k_base is equivalent structure for chunk sizes)
    token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=500,
        chunk_overlap=50
    )
    
    chunks = []
    print("Splitting text into token chunks...")
    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_num = page_idx + 1
        text = page.get_text()
        
        if not text.strip():
            continue
            
        # Split page text into chunks
        page_chunks = token_splitter.split_text(text)
        for chunk_idx, chunk_text in enumerate(page_chunks):
            chunks.append({
                "text": chunk_text,
                "page_number": page_num,
                "chunk_index": chunk_idx
            })
            
    total_chunks = len(chunks)
    print(f"[OK] Generated {total_chunks} chunks from {total_pages} pages.")
    
    # 6. Embed and Upload in Batches
    print("\nStarting batch vector embeddings and upload to Pinecone...")
    batch_size = 100
    
    for i in tqdm(range(0, total_chunks, batch_size), desc="Ingesting Batches"):
        batch = chunks[i : i + batch_size]
        texts = [item["text"] for item in batch]
        
        try:
            # Generate embeddings
            embeds = embeddings.embed_documents(texts)
            
            # Form Pinecone vector payloads
            vectors = []
            for j, item in enumerate(batch):
                # Unique ID representing page and chunk
                vector_id = f"chunk_p{item['page_number']}_c{item['chunk_index']}_{i + j}"
                vectors.append((
                    vector_id,
                    embeds[j],
                    {
                        "text": item["text"],
                        "page_number": item["page_number"],
                        "chunk_index": item["chunk_index"]
                    }
                ))
                
            # Upsert vectors
            index.upsert(vectors=vectors)
            
        except Exception as e:
            print(f"\nERROR: Failed during batch starting at index {i}: {str(e)}")
            print("Stopping ingestion. You can run the script again once fixed.")
            sys.exit(1)
            
    print("\n" + "=" * 60)
    print(f"[OK] INGESTION COMPLETED. Successfully loaded {total_chunks} vectors into Pinecone!")
    print("=" * 60)

if __name__ == "__main__":
    run_ingestion()
