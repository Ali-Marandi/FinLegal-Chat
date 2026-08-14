# FinLegal-Chat

Desktop prototype for **licensed lawyers and in-house counsel** to ask questions about uploaded financial or legal documents (PDF, DOCX, TXT).

**This is not a lawyer. It is not legal advice.** Do not rely on an answer until a qualified lawyer has reviewed it.

**این خروجی هوش مصنوعی است، مشاوره حقوقی نیست، و باید توسط وکیل دارای پروانه بررسی شود.**

## What it does

- Upload PDF / DOCX / TXT
- Index the text with FAISS
- Answer with GPT-4o (cloud) or Llama 3 through local Ollama
- Optionally export a Word or Excel summary

It does not represent a client, file anything with a court, or replace a licensed professional.

## Run

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...   # cloud mode
python main.py
```

Local mode expects Ollama at `http://localhost:11434` with Llama 3.

## Stack

Flet, LangChain / LangGraph, FAISS, OpenAI or Ollama, python-docx, openpyxl.

## License

MIT
