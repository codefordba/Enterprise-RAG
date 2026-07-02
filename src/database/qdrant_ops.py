import json
import urllib.request
import urllib.error
from src.config import Config

class QdrantTenantManager:
    def __init__(self):
        self.base_url = f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}/collections/{Config.COLLECTION_NAME}"

    def initialize_collection(self):
        print(f"🛠️ Configuring schema collection framework for: '{Config.COLLECTION_NAME}'...")
        payload = {
            "vectors": {"size": Config.VECTOR_DIMENSION, "distance": "Cosine"},
            "hnsw_config": {"m": 0, "payload_m": 16}
        }
        try:
            req = urllib.request.Request(
                self.base_url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="PUT"
            )
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode("utf-8"))
                print(f"✅ Collection initialized: {res.get('status')}")
            self._create_tenant_payload_index()
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode("utf-8")
            if "already exists" in error_msg:
                print(f"ℹ️ Collection '{Config.COLLECTION_NAME}' already exist in cluster layout.")
            else:
                print(f"❌ Schema execution error: {error_msg}")

    def _create_tenant_payload_index(self):
        url = f"{self.base_url}/index"
        payload = {
            "field_name": "tenant_id",
            "field_schema": {"type": "keyword", "is_tenant": True}
        }
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode("utf-8"))
                print(f"✅ HNSW tenant segmentation schema mapped: {res.get('status')}")
        except Exception as e:
            print(f"❌ Index configuration fault: {str(e)}")

if __name__ == "__main__":
    Config.print_runtime_summary()
    manager = QdrantTenantManager()
    manager.initialize_collection()