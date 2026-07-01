# src/main.py
import os
import streamlit as st
from src.database.qdrant_ops import QdrantManager
from src.database.query_engine import MultiTenantQueryEngine
from src.processing.layout_parser import LayoutAwareParser
from src.processing.semantic_splitter import SemanticProcessingEngine

# Page Layout Setup - Premium Dark/Light Adaptive Configuration
st.set_page_config(page_title="Enterprise RAG Control Center", layout="wide", initial_sidebar_state="expanded")

# Initialize and persist available dynamic tenant schemas in UI session memory
if "available_tenants" not in st.session_state:
    st.session_state.available_tenants = ["finance_reasoning", "legal_analysis", "tech_support", "hr_policy"]

# Bootstrap backend managers safely
@st.cache_resource
def bootstrap_backend():
    db_manager = QdrantManager()
    db_manager.initialize_schema()
    processing_engine = SemanticProcessingEngine()
    query_engine = MultiTenantQueryEngine()
    return db_manager, processing_engine, query_engine

try:
    db, engine, search_engine = bootstrap_backend()
except Exception:
    st.error("Could not bind localized container microservices. Ensure Docker stack is live.")
    st.stop()

# --- SIDEBAR: TARGET CONTROLLER SPACE ---
st.sidebar.markdown("## 🏢 Workspace Context")
active_tenant = st.sidebar.selectbox(
    "Active Tenant Schema",
    options=st.session_state.available_tenants,
    help="Routes all vector actions to this specific customer payload partition."
)

# Live accounting metrics computed directly from Qdrant HNSW data partitions
tenant_chunks = db.get_tenant_vector_count(active_tenant)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Partition Status")
st.sidebar.metric(label="Ingested Chunks", value=f"{tenant_chunks} Nodes")
st.sidebar.info(f"Currently connected to cluster partition mapping: `{active_tenant}`")


# --- MAIN INTERFACE DISPLAY ---
st.title("⚙️ Enterprise RAG Platform Hub")
st.caption("Production-Grade Multi-Tenant Layout Parsing & Context Retrieval Gateway")

# Application Navigation Tabs
tab_ingest, tab_query, tab_schema = st.tabs([
    "📥 Document Ingestion", 
    "🔍 Query Sandbox", 
    "🛠️ Schema Management"
])

# ==========================================
# TAB 1: PRODUCTION INGESTION LIFECYCLE
# ==========================================
with tab_ingest:
    st.markdown(f"### Ingest Documentation into `{active_tenant}`")
    st.info("Uploaded files will be processed with layout-aware parsing and split using sentence embedding distances.")
    
    uploads = st.file_uploader(
        "Drop Enterprise PDF files here", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="uploader_widget"
    )
    
    if uploads:
        if st.button("Execute Ingestion Loop", type="primary", use_container_width=True):
            for upload in uploads:
                with st.spinner(f"Extracting layouts for: {upload.name}..."):
                    temp_disk_path = os.path.join("/tmp", f"ui_{upload.name}")
                    with open(temp_disk_path, "wb") as buffer:
                        buffer.write(upload.getbuffer())
                    
                    try:
                        raw_blocks = LayoutAwareParser.extract_elements(temp_disk_path)
                        points = engine.generate_points(raw_blocks, active_tenant, upload.name)
                        
                        if points:
                            db.upsert_chunks(points)
                            st.success(f"Successfully committed {len(points)} vector nodes for '{upload.name}'!")
                        else:
                            st.warning(f"File '{upload.name}' generated no text segments.")
                    except Exception as ex:
                        st.error(f"Failed to ingest '{upload.name}': {str(ex)}")
                    finally:
                        if os.path.exists(temp_disk_path):
                            os.remove(temp_disk_path)
            st.rerun()

# ==========================================
# TAB 2: INTERACTIVE QUERY PLAYGROUND
# ==========================================
with tab_query:
    st.markdown(f"### Query Playground Context Partition: `{active_tenant}`")
    
    user_query = st.text_input(
        "Enter natural language probe query", 
        placeholder="e.g., What are the contractual baseline metrics or caps?",
        key="playground_search"
    )
    
    search_limit = st.slider("Max Return Context Constraints (Limit)", min_value=1, max_value=5, value=3)
    
    if st.button("Run Similarity Retrieval Pass", type="secondary", use_container_width=True):
        if not user_query.strip():
            st.warning("Please input a valid textual query string.")
        else:
            with st.spinner("Computing query embeddings and matching points..."):
                results = search_engine.retrieve_context(user_query, active_tenant, limit=search_limit)
                
                if not results:
                    st.info("Vector query executed successfully, but returned zero isolated records for this tenant context.")
                else:
                    st.markdown("#### 🎯 Closest Matching Context Passages")
                    for i, match in enumerate(results, start=1):
                        with st.container(border=True):
                            col1, col2, col3 = st.columns(3)
                            col1.markdown(f"**Match Relevance Rank:** #{i}")
                            col2.markdown(f"**Similarity Score:** `{match['score']:.4f}`")
                            col3.markdown(f"**Structure Type:** `{match['chunk_type'].upper()}`")
                            
                            st.markdown(f"**Context Payload:**")
                            st.code(match['text'], language="text")
                            st.caption(f"Source Lineage Reference: {match['source_file']} | Page Element Pointer: {match['page_number']}")

# ==========================================
# TAB 3: CONTROL LAYER (SCHEMA MANAGEMENT)
# ==========================================
with tab_schema:
    st.markdown("### 🛠️ Cluster Schema Configuration Manager")
    
    # 1. CREATE SCHEMA SECTION
    st.markdown("#### Create New Tenant Schema Partition")
    col_create_input, col_create_btn = st.columns([3, 1])
    new_schema_name = col_create_input.text_input(
        "Provide Unique Alphanumeric Schema Key", 
        placeholder="e.g., compliance_division",
        key="create_schema_input"
    ).strip().lower()
    
    if col_create_btn.button("Register Schema", type="secondary", use_container_width=True):
        if not new_schema_name:
            st.error("Schema names cannot be empty strings.")
        elif new_schema_name in st.session_state.available_tenants:
            st.warning(f"Schema configuration partition target '{new_schema_name}' is already active.")
        else:
            st.session_state.available_tenants.append(new_schema_name)
            st.success(f"Successfully built schema tenant registry endpoint mapping: `{new_schema_name}`")
            st.rerun()
            
    st.markdown("---")
    
    # 2. TRUNCATE DATA SECTION
    st.markdown("#### Truncate Active Schema Vectors")
    st.warning(f"Warning: Truncating will clear all vector data points registered to `{active_tenant}`. This action is irreversible.")
    if st.button(f"Truncate Data for `{active_tenant}`", type="primary", key="truncate_btn"):
        with st.spinner(f"Purging active vector entries for partition `{active_tenant}`..."):
            db.purge_tenant_data(active_tenant)
            st.success(f"Data mapping index reset completed for tenant context: `{active_tenant}`")
            st.timer = 2
            st.rerun()
            
    st.markdown("---")
    
    # 3. DELETE SCHEMA SECTION
    st.markdown("#### Deregister & Drop Entire Tenant Schema")
    st.error(f"Danger Zone: Deleting will wipe all data points for `{active_tenant}` and completely remove the tenant mapping option from the platform portal.")
    if st.button(f"Permanently Delete `{active_tenant}`", key="delete_schema_btn"):
        if len(st.session_state.available_tenants) <= 1:
            st.error("System constraint block: Cannot drop all schema paths. At least 1 tracking context must remain active.")
        else:
            with st.spinner(f"Wiping records and removing tenant registration for `{active_tenant}`..."):
                # Clean database space first
                db.purge_tenant_data(active_tenant)
                # Unbind registry tracker from layout session configurations
                st.session_state.available_tenants.remove(active_tenant)
                st.success(f"Deregistered context map target '{active_tenant}' completely.")
                st.rerun()