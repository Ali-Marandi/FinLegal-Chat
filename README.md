# FinLegal-Chat Ultimate v5.0.0

<p align="center">
  <strong>AI-Powered Legal & Financial Intelligence Platform</strong>
</p>

---

## Overview

FinLegal-Chat Ultimate is a commercial-grade desktop application that combines multi-agent AI reasoning with full-scale document automation for legal, financial, and market analysis. Designed for professionals who demand precision, security, and efficiency.

## Features

### Multi-Agent AI Engine
- **Legal Expert**: Contracts, compliance, and international law analysis
- **Financial Strategist**: Fiscal analysis, trend forecasting, data extraction
- **Market Analyst**: Global shifts, regulatory changes, competitive landscape
- **Risk Manager**: Threat identification, mitigation strategies, cascading risk detection
- **Executive Synthesizer**: Consolidated executive reports with actionable insights

### Professional UI
- Premium dark theme with gold accents
- Persistent chat history with session management
- Sidebar navigation with pinned sessions
- Right panel for document and report management
- Real-time progress tracking for AI pipeline
- Markdown rendering with syntax highlighting

### Document Intelligence
- High-fidelity ingestion: PDF, DOCX, TXT, CSV
- Semantic chunking with layout awareness
- FAISS-powered vector retrieval
- Automated Word and Excel report generation
- Interactive data visualization

### Security & Privacy
- **Cloud Mode**: OpenAI GPT-4o for maximum reasoning
- **Local Mode**: Ollama (Llama 3) for absolute data privacy
- Secure local credential storage
- No data leaves your machine in Local Mode

## Quick Start

### Download

Download the latest `FinLegal-Chat-Ultimate-Windows.zip` from the [Releases](https://github.com/Ali-Marandi/FinLegal-Chat/releases) page.

### Run
1. Extract the ZIP archive
2. Run `FinLegal-Chat-Ultimate.exe`
3. Go to **Settings** and enter your OpenAI API key (or switch to Local Mode)
4. Upload documents using the sidebar or the attach button
5. Ask your legal, financial, or market questions

### Requirements
- Windows 10/11 (64-bit)
- 4 GB RAM (8 GB recommended)
- Internet connection (Cloud Mode)
- [Ollama](https://ollama.ai) (Local Mode)

## Development

```bash
# Clone
gh repo clone Ali-Marandi/FinLegal-Chat
cd FinLegal-Chat

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

## Architecture

```
FinLegal-Chat/
├── main.py              # Entry point
├── src/
│   ├── config.py        # Settings management
│   ├── database.py      # SQLite persistence
│   ├── engine.py        # Multi-agent AI pipeline
│   ├── automation.py    # Document generation
│   └── ui/
│       ├── theme.py     # Professional theme system
│       ├── components.py # Reusable UI widgets
│       ├── app.py       # Main application controller
│       └── screens/
│           ├── chat_screen.py
│           ├── settings_screen.py
│           ├── documents_screen.py
│           └── history_screen.py
├── .github/workflows/   # CI/CD
└── FinLegal-Chat.spec   # PyInstaller build config
```

## Technology Stack

| Component | Technology |
-----------|------------|
| Frontend | Flet (Material Design 3) |
| AI Orchestration | LangGraph (Multi-Agent DAG) |
| LLM | OpenAI GPT-4o / Ollama (Llama 3) |
| Vector Store | FAISS |
| Document Gen | python-docx, openpyxl |
| Database | SQLite3 (WAL mode) |
| Packaging | PyInstaller |

## License

MIT License