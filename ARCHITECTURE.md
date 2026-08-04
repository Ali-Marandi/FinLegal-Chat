# FinLegal-Chat Pro: Revolutionary AI Architecture (v2.0)

## 1. Overview

FinLegal-Chat Pro (v2.0) is a state-of-the-art AI assistant specifically engineered for the high-stakes environments of Finance and Law. Unlike traditional RAG systems, it employs an **Agentic Workflow** that allows the AI to reason, self-correct, and analyze complex data structures like financial tables with human-like precision.

## 2. Revolutionary Components

### 2.1. Agentic RAG Core (LangGraph)
The heart of the application is a directed acyclic graph (DAG) built with LangGraph. It consists of:
*   **Retriever Node**: Fetches initial context from the FAISS vector store.
*   **Grader Node**: An LLM-based judge that assesses the relevance of retrieved documents.
*   **Query Transformer**: If retrieval is poor, this node rewrites the user query to optimize for semantic search.
*   **Generator Node**: Synthesizes the final answer, citing specific context.

### 2.2. Intelligent Data Visualization
The system includes a **Data Analyst Agent** that:
*   Detects financial figures and temporal data within documents.
*   Automatically structures this data into JSON format.
*   Renders interactive **Plotly charts** directly in the chat interface, allowing for instant trend analysis.

### 2.3. Hybrid Privacy Engine
To meet the strict compliance requirements of legal and financial firms, the engine supports two modes:
*   **Cloud Mode (OpenAI)**: Uses GPT-4o for maximum reasoning power.
*   **Privacy Mode (Local LLM)**: Connects to a local Ollama instance (e.g., Llama 3) to ensure that sensitive documents never leave the user's machine.

### 2.4. High-Fidelity Ingestion
Uses a multi-stage parsing strategy:
*   **Semantic Chunking**: Breaks documents into meaningful sections rather than arbitrary character counts.
*   **Layout Awareness**: Preserves the relationship between table headers and data points.

## 3. Advanced UI/UX
The interface is built with Flet and follows "Pro-Dark" design principles:
*   **Interactive Chat**: Supports rich text, code blocks, and embedded charts.
*   **Real-time Feedback**: Progress bars and status indicators for agentic reasoning steps.
*   **Configuration Dashboard**: Easy switching between cloud and local modes.

## 4. CI/CD & Distribution
The application is automatically packaged into a standalone Windows `.exe` via GitHub Actions, ensuring that the latest "Pro" features are always available for download in the Releases section.
