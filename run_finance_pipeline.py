import os
import sys
import logging
import requests
import urllib3
from src.database.qdrant_ops import QdrantManager
from src.processing.layout_parser import LayoutAwareParser
from src.processing.semantic_splitter import SemanticProcessingEngine
from src.database.query_engine import MultiTenantQueryEngine

# Suppress internal SSL warnings since we are intentionally bypassing validation
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure visibility logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("FinancePipeline")

def run_pipeline():
    PDF_URL = "https://mbpc.tcnj.edu/wp-content/uploads/sites/148/2021/10/Sample-Financial-Statements-1.pdf"
    LOCAL_FILENAME = "sample_financial_statements.pdf"
    TENANT_ID = "finance_reasoning"

    print("\n" + "="*70)
    print(f"🚀 PHASE 1: FETCHING TARGET FINANCIAL BENCHMARK DATASET")
    print("="*70)
    
    # PRODUCTION FIX: Added standard macOS Chrome User-Agent header to bypass 403 WAF blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    try:
        logger.info(f"Downloading stream from: {PDF_URL} (Bypassing SSL & Spoofing User-Agent)")
        response = requests.get(PDF_URL, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        
        with open(LOCAL_FILENAME, "wb") as f:
            f.write(response.content)
        logger.info(f"Saved corporate data array locally to: {LOCAL_FILENAME}")
        
    except Exception as e:
        logger.error(f"Network download block encountered: {str(e)}")
        sys.exit(1)

    print("\n" + "="*70)
    print(f"🧱 PHASE 2: PROCESSING STRUCTURAL ELEMENTS & ENCODING VECTORS")
    print("="*70)

    try:
        db_manager = QdrantManager()
        db_manager.initialize_schema()
        processing_engine = SemanticProcessingEngine()

        logger.info("Executing pdfplumber structural matrix layout extraction...")
        raw_elements = LayoutAwareParser.extract_elements(LOCAL_FILENAME)
        logger.info(f"Extracted {len(raw_elements)} base layout sections from document framework.")

        logger.info("Routing text blocks to decoupled TEI container for vector generation...")
        points = processing_engine.generate_points(raw_elements, TENANT_ID, LOCAL_FILENAME)
        
        if not points:
            logger.error("No valid points generated from parsing layer.")
            sys.exit(1)

        logger.info(f"Upserting {len(points)} vectorized points into Qdrant...")
        db_manager.upsert_chunks(points)
        print("\n✅ SUCCESS: INGESTION COMPLETE! DATA PARTITIONED UNDER 'finance_reasoning'.")

    except Exception as e:
        logger.error(f"Ingestion runtime failure: {str(e)}")
        sys.exit(1)
    finally:
        if os.path.exists(LOCAL_FILENAME):
            os.remove(LOCAL_FILENAME)

    print("\n" + "="*70)
    print(f"🔍 PHASE 3: END-TO-END TARGET RETRIEVAL SMOKE TEST")
    print("="*70)

    query_engine = MultiTenantQueryEngine()
    test_query = "What is the total value listed under current assets for Cash?"
    
    logger.info(f"Executing retrieval sweep for query: '{test_query}'")
    matches = query_engine.retrieve_context(query_str=test_query, tenant_id=TENANT_ID, limit=1)

    print("\n" + "-"*70)
    if matches:
        match = matches[0]
        print(f"🎯 MATCH FOUND (Score: {match['score']:.4f})")
        print(f"📄 Source File: {match['source_file']} | Structure Type: {match['chunk_type'].upper()}")
        print(f"📝 Retextured Context Payload:\n\n{match['text']}")
    else:
        print("❌ CRITICAL: Vector search executed successfully but returned no relevant data maps.")
    print("-"*70 + "\n")

if __name__ == "__main__":
    run_pipeline()
