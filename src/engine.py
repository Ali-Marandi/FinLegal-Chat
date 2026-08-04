import os
from typing import List, Dict, TypedDict, Annotated, Sequence
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langchain_core.output_parsers import JsonOutputParser
import operator

# --- State Definition ---
class AgentState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    chart_data: Dict
    steps: List[str]

class FinLegalEngine:
    def __init__(self, mode="openai", local_url="http://localhost:11434"):
        self.mode = mode
        if mode == "openai":
            self.embeddings = OpenAIEmbeddings()
            self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        else:
            from langchain_community.embeddings import OllamaEmbeddings
            from langchain_community.chat_models import ChatOllama
            self.embeddings = OllamaEmbeddings(base_url=local_url, model="llama3")
            self.llm = ChatOllama(base_url=local_url, model="llama3", temperature=0)
            
        self.vector_store = None
        self.workflow = self._build_workflow()

    def ingest_document(self, file_path: str):
        """Advanced ingestion with high-fidelity parsing."""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        documents = loader.load()
        
        # Semantic chunking strategy
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""]
        )
        texts = text_splitter.split_documents(documents)
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
        else:
            self.vector_store.add_documents(texts)

    def _build_workflow(self):
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("grade_documents", self._grade_documents)
        workflow.add_node("generate", self._generate)
        workflow.add_node("transform_query", self._transform_query)

        # Build graph
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self._decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": "generate",
            },
        )
        workflow.add_edge("transform_query", "retrieve")
        workflow.add_edge("generate", END)

        return workflow.compile()

    # --- Node Functions ---
    def _retrieve(self, state: AgentState):
        print("---RETRIEVING---")
        question = state["question"]
        documents = self.vector_store.as_retriever(search_kwargs={"k": 4}).invoke(question)
        return {"documents": documents, "question": question}

    def _grade_documents(self, state: AgentState):
        print("---CHECKING RELEVANCE---")
        question = state["question"]
        documents = state["documents"]
        
        # LLM Grader
        prompt = ChatPromptTemplate.from_template(
            "You are a grader assessing relevance of a retrieved document to a user question. \n"
            "If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n"
            "Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question.\n"
            "Question: {question} \nDocument: {document}"
        )
        grader_chain = prompt | self.llm
        
        relevant_docs = []
        for d in documents:
            res = grader_chain.invoke({"question": question, "document": d.page_content})
            if "yes" in res.content.lower():
                relevant_docs.append(d)
        
        return {"documents": relevant_docs, "question": question}

    def _generate(self, state: AgentState):
        print("---GENERATING---")
        question = state["question"]
        documents = state["documents"]
        
        prompt = ChatPromptTemplate.from_template(
            "You are an expert financial and legal assistant. Answer the question based ONLY on the provided context. \n"
            "If the answer involves multiple financial figures across time or categories, also provide a JSON block for a chart. \n"
            "Format for chart JSON: {\"type\": \"bar|line\", \"title\": \"...\", \"labels\": [], \"values\": []} \n"
            "Context: {context} \nQuestion: {question}"
        )
        gen_chain = prompt | self.llm
        
        context = "\n\n".join([d.page_content for d in documents])
        res = gen_chain.invoke({"context": context, "question": question})
        
        # Simple extraction of JSON for chart if present
        chart_data = None
        import json
        import re
        try:
            match = re.search(r'\{.*"values".*\}', res.content, re.DOTALL)
            if match:
                chart_data = json.loads(match.group())
                clean_content = res.content.replace(match.group(), "").strip()
            else:
                clean_content = res.content
        except:
            clean_content = res.content

        return {"generation": clean_content, "chart_data": chart_data}

    def _transform_query(self, state: AgentState):
        print("---TRANSFORMING QUERY---")
        question = state["question"]
        
        prompt = ChatPromptTemplate.from_template(
            "You are a query re-writer that optimizes a question for vectorstore retrieval. \n"
            "Look at the input and try to reason about the underlying semantic intent / meaning. \n"
            "Initial question: {question}"
        )
        re_writer_chain = prompt | self.llm
        res = re_writer_chain.invoke({"question": question})
        return {"question": res.content}

    def _decide_to_generate(self, state: AgentState):
        if not state["documents"]:
            return "transform_query"
        return "generate"

    def query(self, question: str) -> Dict:
        if self.vector_store is None:
            return {"answer": "Please upload documents first.", "chart": None}
        
        inputs = {"question": question, "steps": []}
        config = {"recursion_limit": 10}
        result = self.workflow.invoke(inputs, config)
        return {"answer": result["generation"], "chart": result.get("chart_data")}

    def reset(self):
        self.vector_store = None
