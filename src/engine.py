import os
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class FinLegalEngine:
    def __init__(self):
        # Use provided OpenAI API Key via environment variable
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
        self.vector_store = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.qa_chain = None

    def ingest_document(self, file_path: str):
        """Load and index a document with support for PDF, TXT, and DOCX."""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        documents = loader.load()
        
        # Professional chunking for legal/financial docs
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        texts = text_splitter.split_documents(documents)
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
        else:
            self.vector_store.add_documents(texts)
        
        # Initialize/Update Conversational Chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory
        )

    def query(self, question: str) -> str:
        """Answer a question with conversation memory."""
        if self.qa_chain is None:
            return "Please upload a document first to start the analysis."
        
        try:
            response = self.qa_chain.invoke({"question": question})
            return response['answer']
        except Exception as e:
            return f"Error during analysis: {str(e)}"

    def reset(self):
        """Clear memory and vector store."""
        self.vector_store = None
        self.memory.clear()
        self.qa_chain = None
