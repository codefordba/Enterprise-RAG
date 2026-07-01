# src/config.py
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

@dataclass(frozen=True)
class AppConfig:
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "tenant_knowledge_base")
    EMBEDDING_API_URL: str = os.getenv("EMBEDDING_API_URL", "http://localhost:8080")
    VECTOR_SIZE: int = 1024

settings = AppConfig()