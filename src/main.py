import streamlit as st
import urllib.request
import json
from src.config import Config
from src.generation.orchestrator import ContextOrchestrator
from src.processing.ingest_pipeline import TenantIngestionPipeline

st.set_page_config(page_title="Enterprise-RAG Ops Console", page_icon="🏛️", layout="wide")

if "tenant_adapter_map" not in st.session_state:
    st.session_state.tenant_adapter_map = {
        "finance_reasoning": "finance_reasoning",
        "tech_support": "tech_support"
    }

class CoreOperationsCenterApp:
    def __init__(self):
        self.orchestrator = ContextOrchestrator()

    def _check_node_health(self, url: str, method: str = "GET") -> bool:
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=2):
                return True
        except Exception:
            return False

    def _fetch_live_vllm_adapters(self) -> list:
        url = f"{Config.LLM_API_BASE_URL}/models"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as res:
                data = json.loads(res.read().decode("utf-8"))
                return [model["id"] for model in data.get("data", [])]
        except Exception:
            return list(set(st.session_state.tenant_adapter_map.values()))

    def render_sidebar_status(self):
        with st.sidebar:
            st.title("🏛️ Cluster Registry")
            st.markdown("---")
            st.subheader("📡 Live Node Telemetry")
            
            q_health = self._check_node_health(f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}/readyz")
            t_health = self._check_node_health(Config.TEI_ENDPOINT.split("/embed")[0], method="HEAD")
            v_health = self._check_node_health(f"{Config.LLM_API_BASE_URL}/models")

            st.markdown(f"**Qdrant Node:** `:{Config.QDRANT_PORT}` " + ("🟢 ONLINE" if q_health else "🔴 UNREACHABLE"))
            st.markdown(f"**Embedding Node:** `:8080` " + ("🟢 ONLINE" if t_health else "🔴 UNREACHABLE"))
            st.markdown(f"**vLLM Cluster:** `:8000` " + ("🟢 ONLINE" if v_health else "🔴 UNREACHABLE"))
            
            st.markdown("---")
            if st.button("🔄 Refresh System Node States", use_container_width=True):
                st.rerun()

            st.markdown("---")
            st.subheader("🔑 Active Context Boundary")
            st.session_state.current_tenant = st.selectbox(
                "Current Active Tenant Focus:",
                options=list(st.session_state.tenant_adapter_map.keys()),
                format_func=lambda x: f"🏢 {x.upper()}"
            )
            active_adapter = st.session_state.tenant_adapter_map[st.session_state.current_tenant]
            st.info(f"Routed Adapter: `{active_adapter}`")

    def render_tenant_admin_tab(self):
        st.header("🧱 Dynamic Tenant Provisioning & LoRA Matrix Setup")
        st.write("Manage client workspace partitions and bind them directly to hardware adapter profiles.")
        
        add_col, del_col = st.columns(2)
        with add_col:
            st.subheader("✨ Provision New Corporate Tenant")
            with st.form("create_tenant_form", clear_on_submit=True):
                new_id = st.text_input("New Tenant Registry Key Unique Name:", placeholder="e.g., legal_compliance").strip()
                live_hardware_adapters = self._fetch_live_vllm_adapters()
                new_lora = st.selectbox("Select Target LoRA Adapter Module Matrix:", options=live_hardware_adapters)
                
                if st.form_submit_button("🔨 Initialize Tenant Domain Key"):
                    if new_id and new_lora:
                        st.session_state.tenant_adapter_map[new_id] = new_lora
                        st.success(f"🎉 Tenant registry configured successfully! Domain Key [{new_id.upper()}] active.")
                        st.rerun()
                    else:
                        st.error("Fields cannot stand empty during provisioning loops.")
                        
        with del_col:
            st.subheader("🗑️ Deprovision Isolated Tenant Matrix")
            target_del = st.selectbox("Select Target Tenant to Purge:", options=list(st.session_state.tenant_adapter_map.keys()))
            if st.button("❌ Terminate Tenant Workspace", type="primary", use_container_width=True):
                purge_payload = {"filter": {"must": [{"key": "tenant_id", "match": {"value": target_del}}]}}
                try:
                    urllib.request.urlopen(urllib.request.Request(
                        f"http://{Config.QDRANT_HOST}:{Config.QDRANT_PORT}/collections/{Config.COLLECTION_NAME}/points/delete",
                        data=json.dumps(purge_payload).encode("utf-8"), headers={"Content-Type":"application/json"}, method="POST"
                    ))
                except Exception:
                    pass
                del st.session_state.tenant_adapter_map[target_del]
                st.warning(f"💥 Workspace and all underlying vector footprints for [{target_del.upper()}] destroyed.")
                st.rerun()

    def render_data_feed_tab(self):
        st.header("📥 Document & Spreadsheet Processing Panel")
        st.write(f"Target Cluster Workspace Boundary: **[{st.session_state.current_tenant.upper()}]**")
        
        uploaded_file = st.file_uploader("Upload Target Document / Spreadsheet Assets:", type=["pdf", "xlsx", "xls"])
        
        if uploaded_file is not None:
            file_ext = uploaded_file.name.split(".")[-1].lower()
            st.info(f"Asset Loaded: `{uploaded_file.name}` ({uploaded_file.size / 1024:.2f} KB)")
            
            # Auto-suggest a clean default family key from the filename string
            suggested_family = uploaded_file.name.split(".")[0].split("_v")[0].split("202")[0].strip("_").lower()
            
            # --- EXTENDED LINEAGE INPUT FIELD FOR SCENARIO 3 VERSION CONTROL ---
            ui_family_key = st.text_input(
                "📋 Document Lineage Identifier / Family Tracking Key:",
                value=suggested_family,
                help="Documents with matching tracking keys are treated as version updates. The old data points will be replaced automatically, even if the new file has a different name."
            )
            
            if st.button("⚡ Start Layout-Aware Vector Ingestion", type="primary"):
                raw_pages = []
                
                if file_ext == "pdf":
                    with st.spinner("Extracting multi-page text and tabular layers..."):
                        try:
                            import pdfplumber
                        except ImportError:
                            st.error("Please run `pip install pdfplumber` on your host terminal.")
                            return

                        with pdfplumber.open(uploaded_file) as pdf:
                            for idx, page in enumerate(pdf.pages, 1):
                                text_body = page.extract_text() or ""
                                table_md_accumulate = []
                                tables = page.extract_tables() or []
                                for tbl in tables:
                                    if not tbl: continue
                                    cleaned_rows = [[str(cell).strip() if cell is not None else "" for cell in r] for r in tbl]
                                    if len(cleaned_rows) > 1:
                                        headers = cleaned_rows[0]
                                        m_str = f"| {' | '.join(headers)} |\n| {' | '.join(['---'] * len(headers))} |\n"
                                        for row in cleaned_rows[1:]:
                                            m_str += f"| {' | '.join(row)} |\n"
                                        table_md_accumulate.append(m_str)

                                raw_pages.append({
                                    "page_number": idx,
                                    "text": text_body,
                                    "table_markdown": "\n\n".join(table_md_accumulate)
                                })

                elif file_ext in ["xlsx", "xls"]:
                    with st.spinner("Parsing workbook layers and layout grids..."):
                        try:
                            import pandas as pd
                        except ImportError:
                            st.error("Missing libraries: Run `pip install pandas openpyxl` to enable Excel ingestion.")
                            return

                        try:
                            excel_workbook = pd.ExcelFile(uploaded_file)
                            for sheet_idx, sheet_name in enumerate(excel_workbook.sheet_names, 1):
                                df = excel_workbook.parse(sheet_name)
                                if df.empty: continue
                                df = df.fillna("")
                                headers = [str(col).strip() for col in df.columns]
                                
                                md_grid = f"### SPREADSHEET WORKBOOK TAB: {sheet_name.upper()}\n"
                                md_grid += f"| {' | '.join(headers)} |\n| {' | '.join(['---'] * len(headers))} |\n"
                                for _, row in df.iterrows():
                                    row_values = [str(val).strip() for val in row.values]
                                    md_grid += f"| {' | '.join(row_values)} |\n"
                                
                                raw_pages.append({
                                    "page_number": sheet_idx,
                                    "text": f"Structured analytical spreadsheet data contained in workbook worksheet tab: {sheet_name}.",
                                    "table_markdown": md_grid
                                })
                        except Exception as e:
                            st.error(f"Excel File Analysis Interrupted: {str(e)}")
                            return

                if not raw_pages:
                    st.warning("No usable records discovered inside the uploaded asset.")
                    return

                with st.spinner("⚙️ Evaluating lineage indexes and executing atomic updates..."):
                    pipeline = TenantIngestionPipeline(tenant_id=st.session_state.current_tenant)
                    status = pipeline.process_and_upsert(
                        document_name=uploaded_file.name, 
                        raw_pages=raw_pages, 
                        custom_family_key=ui_family_key
                    )
                    
                    if status == "skipped_duplicate":
                        st.warning("ℹ️ System Event: Content match detected. Ingestion bypassed because an identical document version is already stored.")
                    elif status == "ingested_successfully":
                        st.success(f"🎉 Success! Asset '{uploaded_file.name}' mapped into lineage tracking path [{ui_family_key.upper()}].")

    def render_query_playground_tab(self):
        st.header("🔍 Isolated Inference Console & Prompt Sandbox")
        st.write(f"Context Protection Isolation Mode: **[{st.session_state.current_tenant.upper()}]**")
        
        param_col1, param_col2 = st.columns(2)
        with param_col1:
            ui_temp = st.slider("Model Generation Temperature:", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
        with param_col2:
            ui_top_k = st.slider("Top-K Retrieved Database Context Blocks:", min_value=1, max_value=10, value=3, step=1)

        user_query = st.text_input("Execute Data Search Input Query String:", placeholder="Ask anything about data in this workspace...")
        if st.button("🚀 Run Grounded Query Pass", type="primary", use_container_width=True):
            if not user_query: return
            
            with st.spinner("Compiling contextual layers..."):
                active_lora = st.session_state.tenant_adapter_map[st.session_state.current_tenant]
                res = self.orchestrator.generate_answer(
                    tenant_id=st.session_state.current_tenant,
                    target_adapter=active_lora,
                    user_query=user_query,
                    temperature=ui_temp,
                    top_k=ui_top_k
                )
                
                if res.get("status") == "error":
                    st.error(res.get("message"))
                    return

                st.markdown("### 🤖 Grounded Generation Response Output")
                st.info(res.get("answer"))

                metric_col, citation_col = st.columns([1, 2])
                with metric_col:
                    st.markdown("##### ⏱️ Lifecycle Timelines & Footprints")
                    st.metric("Total Execution Time", f"{res.get('latency_seconds')} sec")
                    tk = res.get("token_metrics", {})
                    st.markdown(f"**Context Tokens:** `{tk.get('prompt_tokens', 0)}`")
                    st.markdown(f"**Output Tokens:** `{tk.get('completion_tokens', 0)}`")

                with citation_col:
                    st.markdown("##### 📌 Vector Match Audit Citations & Scores")
                    for idx, cit in enumerate(res.get("citations", []), 1):
                        st.markdown(f"**[{idx}] `{cit['source']}` (Sheet/Page Reference: {cit['page']})**")
                        st.caption(f"🎯 Vector Match Distance Ranking Score: `{cit['score']}`")

    def run(self):
        self.render_sidebar_status()
        t_query, t_feed, t_admin = st.tabs([
            "🔍 Grounded Query Workspace Playground", 
            "📥 Document Processing Feed Panel", 
            "📊 Tenant Space Administration"
        ])
        with t_query: self.run_error_wrapper(self.render_query_playground_tab)
        with t_feed: self.run_error_wrapper(self.render_data_feed_tab)
        with t_admin: self.run_error_wrapper(self.render_tenant_admin_tab)

    def run_error_wrapper(self, render_func):
        try:
            render_func()
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")

if __name__ == "__main__":
    app = CoreOperationsCenterApp()
    app.run()