import os

class Config:
    """Centralized System Configuration Blueprint."""
    _env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(_env_path):
        with open(_env_path, "r") as f:
            for line in f:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#") and "=" in clean_line:
                    key, val = clean_line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

    # --- NODE NETWORK ADAPTERS ---
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tenant_knowledge_base")
    
    TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "http://localhost:8080/embed")
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1024"))
    TEI_TIMEOUT = int(os.getenv("TEI_TIMEOUT", "60"))

    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "http://localhost:8000/v1").rstrip("/")

    # --- CHUNKING TUNING PARAMETERS ---
    CHUNK_MAX_SIZE = int(os.getenv("CHUNK_MAX_SIZE", "1200"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    NOISE_THRESHOLD_GATE = int(os.getenv("NOISE_THRESHOLD_GATE", "60"))
    CLIENT_BATCH_LIMIT = int(os.getenv("CLIENT_BATCH_LIMIT", "8"))