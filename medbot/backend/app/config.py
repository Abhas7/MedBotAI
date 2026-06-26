import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.environ.get("PORT", 5000))
    
    # Supabase config
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    # OpenAI config
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    
    # Pinecone config
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "medbot")

    # Ollama config
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5-coder:7b")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
    # Parse token limit safely handling inline comments
    _predict = os.environ.get("LLM_NUM_PREDICT", "256")
    _predict_clean = _predict.split("#")[0].strip() if _predict else "256"
    LLM_NUM_PREDICT = int(_predict_clean) if _predict_clean else 256
    
    # Parse thread count safely handling inline comments
    _threads = os.environ.get("LLM_NUM_THREAD", "")
    _threads_clean = _threads.split("#")[0].strip() if _threads else ""
    LLM_NUM_THREAD = int(_threads_clean) if _threads_clean else None

    @classmethod
    def validate(cls):
        """Validate that all required configuration variables are set.
        
        Returns a list of missing configuration key names.
        """
        missing = []
        if not cls.SUPABASE_URL or "placeholder" in cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY or "placeholder" in cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not cls.PINECONE_API_KEY or "placeholder" in cls.PINECONE_API_KEY:
            missing.append("PINECONE_API_KEY")
        return missing
