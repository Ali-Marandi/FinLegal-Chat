import os

from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_community.vectorstores import FAISS

from langchain.chains import RetrievalQA



class FinLegalEngine:
  
    def __init__(self):
      
        self.embeddings = OpenAIEmbeddings()
      
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
      
        self.vector_store = None
      
        self.qa_chain = None
      


    def ingest_document(self, file_path: str):
      
        """Load and index a document."""
      
        if file_path.endswith('.pdf'):
          
            loader = PyPDFLoader(file_path)
          
        else:
          
            loader = TextLoader(file_path)
          


        documents = loader.load()
      
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
      
        texts = text_splitter.split_documents(documents)
      


        if self.vector_store is None:
          
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
          
        else:
          
            self.vector_store.add_documents(texts)
          


        self.qa_chain = RetrievalQA.from_chain_type(
          
            llm=self.llm,
          
            chain_type="stuff",
          
            retriever=self.vector_store.as_retriever()
          
        )
      


    def query(self, question: str) -> str:
      
        """Answer a question based on ingested documents."""
      
        if self.qa_chain is None:
          
            return "Please upload a document first."
          
        return self.qa_chain.run(question)
      


if __name__ == "__main__":
  
    # Quick test
  
    engine = FinLegalEngine()
  
    print("Engine initialized.")
  

































