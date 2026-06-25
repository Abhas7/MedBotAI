import logging
from pinecone import Pinecone
from app.config import Config
from langchain_ollama import ChatOllama
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

class MedicalRAGPipeline:
    def __init__(self):
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
            self.index = self.pc.Index(Config.PINECONE_INDEX_NAME)
            
            # Initialize Embeddings client using fastembed for 0-latency local ONNX execution
            self.embeddings = TextEmbedding(model_name="nomic-ai/nomic-embed-text-v1.5")
              
            llm_kwargs = {
                "model": Config.LLM_MODEL,
                "base_url": Config.OLLAMA_BASE_URL,
                "temperature": 0.2,
                "num_ctx": 4096,
                "num_predict": Config.LLM_NUM_PREDICT
            }
            if Config.LLM_NUM_THREAD is not None:
                llm_kwargs["num_thread"] = Config.LLM_NUM_THREAD
                
            self.llm = ChatOllama(**llm_kwargs)
            logger.info("MedicalRAGPipeline initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize MedicalRAGPipeline: {str(e)}")
            raise e
            
    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve top matching chunks from Pinecone."""
        try:
            # Generate query embedding vector using fastembed (ONNX)
            embeddings_generator = self.embeddings.embed([query])
            query_vector = [float(x) for x in list(embeddings_generator)[0]]
            
            # Query Pinecone index
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            return results.get("matches", [])
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            return []
            
    def generate_response(self, query: str, stream: bool = False):
        """Generate answer using RAG pipeline context."""
        matches = self.retrieve(query)
        
        # Hallucination Guard threshold
        # If no matches or the highest similarity score is too low, bypass LLM
        threshold = 0.55
        if not matches or matches[0].get("score", 0.0) < threshold:
            response_text = "I don't know based on the available medical data."
            if stream:
                def text_generator():
                    yield response_text
                return text_generator(), []
            else:
                return {
                    "answer": response_text,
                    "sources": []
                }
                
        # Prepare Context & Sources
        context_excerpts = []
        sources = []
        for match in matches:
            metadata = match.get("metadata", {})
            text = metadata.get("text", "")
            page_num = metadata.get("page_number", "Unknown")
            score = match.get("score", 0.0)
            
            context_excerpts.append(f"[Page {page_num}] (Score: {score:.3f}):\n{text}")
            sources.append({
                "page_number": page_num,
                "text": text,
                "score": score
            })
            
        context_text = "\n\n".join(context_excerpts)
        
        # Formulate prompt instructions
        system_prompt = (
            "You are MedBot, an expert AI medical assistant trained on medical encyclopedias.\n"
            "Your task is to answer the user's question based ONLY on the provided context excerpts.\n"
            "If the context does not contain enough information to answer the question, or if you are unsure, "
            "respond exactly with: 'I don't know based on the available medical data.'\n\n"
            "Rules:\n"
            "1. Rely only on the clear facts mentioned in the context. Do not invent details or assume facts.\n"
            "2. At the end of key sentences or claims, cite the page numbers in brackets, e.g. [Page X].\n"
            "3. Keep your response clear, professional, and well-structured.\n\n"
            f"Context excerpts:\n{context_text}"
        )
        
        messages = [
            ("system", system_prompt),
            ("human", query)
        ]
        
        if stream:
            # Return a generator that yields token contents, and the sources list separately
            def stream_generator():
                try:
                    for chunk in self.llm.stream(messages):
                        if chunk.content:
                            yield chunk.content
                except Exception as e:
                    logger.error(f"Error during LLM streaming: {str(e)}")
                    yield f"\n[Error during generation: {str(e)}]"
            return stream_generator(), sources
        else:
            try:
                response = self.llm.invoke(messages)
                return {
                    "answer": response.content,
                    "sources": sources
                }
            except Exception as e:
                logger.error(f"Error during LLM invocation: {str(e)}")
                return {
                    "answer": f"Error generating response: {str(e)}",
                    "sources": sources
                }
