# Enterprise-RAG

Enterprise-RAG
A production-grade, highly scalable, multi-tenant Retrieval-Augmented Generation (RAG) platform. This system enforces cryptographic data isolation across corporate tenant partitions sharing a single vector database collection, handles complex data layouts like borderless financial tables, and routes context queries to a dynamic Multi-LoRA inference engine running on a unified base LLM model.

🏢 Why "Enterprise" RAG? The Problem vs. The Solution
Standard or naive RAG architectures suffer from three critical flaws that make them unviable for production deployments in enterprise environments:

Cross-Tenant Data Leaks: Storing corporate records for different business domains (Finance, HR, Legal) in a common vector pool can result in compliance violations if query embeddings leak records across domain boundaries.

Structural Document Destruction: Standard parsing splits PDFs by arbitrary character lengths, scrambling formatting blocks and corrupting borderless grid data (like balance sheets).

GPU Resource Crashing (VRAM Exhaustion): Deploying individual fine-tuned LLMs for each department requires immense VRAM footprint allocations, resulting in high infrastructure overhead and frequent Out-of-Memory (OOM) failures.

Enterprise-RAG solves these constraints through algorithmic and architectural modifications:

Logical Multi-Tenancy via Payload Filtering: Enforces strict tenant partitioning inside a single Qdrant collection using HNSW payload graph overrides, eliminating cross-domain leakage without the infrastructure overhead of managing thousands of distinct database collections.

Layout-Aware Parsing: Isolates tabular structures visually and maps them into native markdown grid strings before vectorization.

Dynamic Multi-LoRA Serving: Serves a single INT8-quantized base foundation model in memory, dynamically applying lightweight specialized adapter matrices on a per-request basis.

## Features

- Layout-aware PDF parsing
- Semantic chunking
- Qdrant Vector Database
- Multi-tenant architecture
- Streamlit-based UI
- Docker deployment
- Environment-based configuration

## Project Structure

```
Enterprise-RAG/
├── .env.example
├── docker-compose.yml
├── README.md
├── requirements.txt
└── src/
```

## Status

🚧 Project under active development.
