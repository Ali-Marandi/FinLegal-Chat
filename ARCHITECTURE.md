# FinLegal-Chat Ultimate - Architecture

## System Overview

FinLegal-Chat Ultimate is built on a multi-agent AI architecture orchestrated by LangGraph, with a professional Flet-based desktop UI and persistent SQLite storage.

## Core Components

### 1. AI Engine (`src/engine.py`)
- **LangGraph DAG**: Fan-out/fan-in pattern for parallel agent execution
- **5 Specialized Agents**: Legal, Financial, Market, Risk, and Synthesis
- **FAISS Vector Store**: High-performance semantic retrieval
- **Progress Callbacks**: Real-time UI updates during analysis

### 2. Application Controller (`src/ui/app.py`)
- Central orchestrator managing engine lifecycle, navigation, and state
- Thread-safe query execution (background thread + UI thread sync)
- Session management with SQLite persistence

### 3. Configuration (`src/config.py`)
- JSON-based settings with auto-save
- XOR-obfuscated credential storage
- Cross-platform config directory resolution

### 4. Database (`src/database.py`)
- SQLite with WAL journal mode
- Tables: sessions, messages, documents, app_state
- Thread-local connections for safety

### 5. UI Layer
- **Theme System**: Brand colors, reusable style dictionaries
- **Components**: AnimatedContainer, GlassCard, ChatBubble, ProgressBar, etc.
- **Screens**: Chat, Settings, Documents, History

## AI Pipeline Flow

```
User Query
    → Retrieve (FAISS top-K)
    → [Legal Expert, Financial Expert, Market Analyst]  (parallel)
    → Risk Manager
    → Aggregator (Executive Report)
    → Output + Auto-generated Reports (.docx, .xlsx)
```

## Data Flow

```
Document Upload → Ingestion → Text Splitting → Embedding → FAISS Index
                                                              ↓
User Query → Retriever → Agent Nodes → Final Report → DB + Files
```