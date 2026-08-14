# FinLegal-Chat architecture

Prototype RAG app for document Q&A. Not a legal practice system.

## Flow

1. **Ingest:** PDF (PyPDF), DOCX (docx2txt), or text. RecursiveCharacterTextSplitter, then FAISS.
2. **Retrieve:** top-k chunks for the question.
3. **Generate:** LangGraph nodes draft legal / financial / market / risk notes, then a synthesizer combines them.
4. **Export:** optional Word report and Excel sheet if chart-like JSON is detected.

## Modes

- **Cloud:** OpenAI embeddings + GPT-4o. Requires `OPENAI_API_KEY`. Documents leave the machine.
- **Local:** Ollama embeddings + Llama 3 at `http://localhost:11434`.

## UI

Flet desktop. File picker, chat pane, export list.

## Limits

No user accounts, no audit log, no guaranteed citations, no evaluation set. Treat every answer as unverified.
