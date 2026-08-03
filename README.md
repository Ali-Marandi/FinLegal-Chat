# FinLegal Chat ⚖️💰

**FinLegal Chat** is a commercial-grade AI assistant designed for deep analysis of financial and legal documents. Built with LangChain and state-of-the-art Large Language Models (LLMs), it provides a robust RAG (Retrieval-Augmented Generation) pipeline to help professionals navigate complex contracts and filings.

## 🚀 Key Features

- **Smart RAG Engine**: Ingests PDF and Text documents with high-fidelity indexing using FAISS and OpenAI Embeddings.
- **Interactive Analysis**: Query your documents in natural language to extract clauses, identify risks, and summarize sections.
- **Financial Context Aware**: Optimized for understanding financial terminology and legal jargon.
- **Modern Web Interface**: A clean, responsive UI built with Flask and Tailwind CSS.
- **Secure Processing**: Handles sensitive documents locally within the session context.

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **AI/LLM**: LangChain, OpenAI (GPT-4o)
- **Vector DB**: FAISS (Facebook AI Similarity Search)
- **Document Processing**: PyPDF, Recursive Text Splitting

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ali-Marandi/FinLegal-Chat.git
   cd FinLegal-Chat
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file and add your OpenAI API Key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

4. Run the application:
   ```bash
   python app.py
   ```

## 📖 Usage

1. Open the web interface (default: `http://localhost:5000`).
2. Upload your PDF or Text legal documents via the sidebar.
3. Start chatting! Ask questions like:
   - "What are the termination clauses in this contract?"
   - "Summarize the financial liabilities mentioned in Section 4."
   - "Are there any indemnity risks for the service provider?"

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
