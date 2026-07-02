import json
import time
import urllib.request
from typing import Dict, Any, List
from src.config import Config

class ContextOrchestrator:
    def __init__(self):
        pass

    def _get_query_vector(self, query_text: str) -> List[float]:
        payload = {"inputs": [query_text]}
        try:
            req = urllib.request.Request(
                Config.TEI_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))[0]
        except Exception:
            return [0.0] * Config.VECTOR_DIMENSION

    def _retrieve_context_from_qdrant(self, tenant_id: str, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        url = f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}/collections/{Config.COLLECTION_NAME}/points/search"
        query_vector = self._get_query_vector(query_text)

        payload = {
            "vector": query_vector,
            "limit": top_k,
            "with_payload": True,
            "with_vector": False,
            "filter": {"must": [{"key": "tenant_id", "match": {"value": tenant_id}}]}
        }
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode("utf-8")).get("result", [])
        except Exception:
            return []

    def generate_answer(self, tenant_id: str, target_adapter: str, user_query: str, temperature: float, top_k: int) -> Dict[str, Any]:
        """Executes prompt synthesis under strict grounding and latency tracking hooks."""
        start_time = time.time()
        
        # 1. Gather vector sub-graph candidates with similarity rankings
        points = self._retrieve_context_from_qdrant(tenant_id, user_query, top_k)
        
        context_chunks = []
        citations = []
        for pt in points:
            score = pt.get("score", 0.0) # Mathematical metric match ranking
            payload_data = pt.get("payload", {})
            text_content = payload_data.get("text_content", "")
            if text_content:
                context_chunks.append(text_content)
                citations.append({
                    "source": payload_data.get("source_file", "unknown_source.pdf"),
                    "page": payload_data.get("page_number", "N/A"),
                    "score": round(score, 4)
                })

        flat_context = "\n---\n".join(context_chunks) if context_chunks else "NO VERIFIED CONTEXT DETECTED."
        
        # 2. Build system context container boundaries
        system_instruction = (
            "You are an elite enterprise core engine agent operating within a secure multi-tenant architecture.\n"
            f"Your current operational domain context isolation group is: [TENANT: {tenant_id.upper()}]\n\n"
            "STRICT GROUNDING REGIME:\n"
            "1. Synthesize your answer using ONLY the explicit text context blocks provided below.\n"
            "2. If context is insufficient, state: 'Information missing from current isolated partition data store.'\n"
            "3. Do NOT utilize background parametric weights to extrapolate claims.\n\n"
            f"--- ISOLATED CONTEXT PAYLOAD ---\n{flat_context}\n--------------------------------"
        )

        vllm_endpoint = f"{Config.LLM_API_BASE_URL}/chat/completions"
        vllm_payload = {
            "model": target_adapter, # Dynamic routing identifier targeting specialized LoRA weights
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_query}
            ],
            "temperature": temperature,
            "max_tokens": 1024
        }

        try:
            req = urllib.request.Request(
                vllm_endpoint, data=json.dumps(vllm_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                vllm_res = json.loads(response.read().decode("utf-8"))
                latency_elapsed = time.time() - start_time
                
                return {
                    "status": "success",
                    "answer": vllm_res["choices"][0]["message"]["content"],
                    "citations": citations,
                    "latency_seconds": round(latency_elapsed, 3),
                    "token_metrics": vllm_res.get("usage", {})
                }
        except Exception as e:
            return {"status": "error", "message": f"Hardware infrastructure completion fault: {str(e)}"}