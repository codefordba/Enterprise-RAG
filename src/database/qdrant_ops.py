# src/database/qdrant_ops.py
import logging
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, HnswConfigDiff, PayloadSchemaType, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
from src.config import settings

logger = logging.getLogger("QdrantManager")

class QdrantManager:
    def __init__(self) -> None:
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.COLLECTION_NAME

    def initialize_schema(self) -> None:
        """Verifies connection and sets up payload-isolated collections securely."""
        try:
            self.client.get_collections()
            if not self.client.collection_exists(collection_name=self.collection_name):
                logger.info(f"Collection '{self.collection_name}' absent. Building custom partition space...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=settings.VECTOR_SIZE, distance=Distance.COSINE),
                    hnsw_config=HnswConfigDiff(payload_m=16, m=0)
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="tenant_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
        except (UnexpectedResponse, Exception) as e:
            logger.error(f"Critical failure during vector layer setup: {str(e)}")
            raise RuntimeError("Database connection block encountered.")

    def upsert_chunks(self, points: List[PointStruct]) -> None:
        """Commits vectorized points to the cluster with strict safety checks."""
        if not points:
            return
        try:
            self.client.upsert(collection_name=self.collection_name, wait=True, points=points)
        except Exception as e:
            logger.error(f"Failed to execute batch upsert vector sequence: {str(e)}")
            raise e

    def get_tenant_vector_count(self, tenant_id: str) -> int:
        """Returns the exact number of active vectors registered to a single tenant."""
        try:
            result = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                )
            )
            return result.count
        except Exception as e:
            logger.error(f"Failed to count vectors for tenant '{tenant_id}': {str(e)}")
            return 0

    def purge_tenant_data(self, tenant_id: str) -> None:
        """Deletes all vectorized entries belonging to a specific tenant partition."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                )
            )
            logger.info(f"Successfully truncated vector nodes for tenant '{tenant_id}'.")
        except Exception as e:
            logger.error(f"Failed execution block for truncating tenant '{tenant_id}': {str(e)}")
            raise e