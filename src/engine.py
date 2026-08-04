import os
import json
import re
from typing import List, Dict, TypedDict, Annotated, Sequence, Union
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# --- Advanced State Definition ---
class AgentState(TypedDict):
    question: str
    documents: List[str]
    legal_opinion: str
    financial_analysis: str
    risk_assessment: str
    market_intelligence: str
    final_consensus: str
    chart_data: Dict
    steps: List[str]

class FinLegalEmpireEngine:
    def __init__(self, mode="openai", local_url="http://localhost:11434"):
        self.mode = mode
        if mode == "openai":
            self.embeddings = OpenAIEmbeddings()
            self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
            self.creative_llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
        else:
            from langchain_community.embeddings import OllamaEmbeddings
            from langchain_community.chat_models import ChatOllama
            self.embeddings = OllamaEmbeddings(base_url=local_url, model="llama3")
            self.llm = ChatOllama(base_url=local_url, model="llama3", temperature=0)
            self.creative_llm = self.llm
            
        self.vector_store = None
        self.workflow = self._build_empire_workflow()

    def ingest_document(self, file_path: str):
        """Ultra-high fidelity ingestion."""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=250,
            separators=["\n\n", "\n", " ", ""]
        )
        texts = text_splitter.split_documents(documents)
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
        else:
            self.vector_store.add_documents(texts)

    def _build_empire_workflow(self):
        workflow = StateGraph(AgentState)

        # Define specialized expert nodes
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("legal_expert", self._legal_expert)
        workflow.add_node("financial_expert", self._financial_expert)
        workflow.add_node("risk_manager", self._risk_manager)
        workflow.add_node("market_researcher", self._market_researcher)
        workflow.add_node("aggregator", self._aggregator)

        # Build graph: Parallel analysis -> Aggregation
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "legal_expert")
        workflow.add_edge("retrieve", "financial_expert")
        workflow.add_edge("retrieve", "market_researcher")
        workflow.add_edge("legal_expert", "risk_manager")
        workflow.add_edge("financial_expert", "risk_manager")
        workflow.add_edge("market_researcher", "risk_manager")
        workflow.add_edge("risk_manager", "aggregator")
        workflow.add_edge("aggregator", END)

        return workflow.compile()

    def _retrieve(self, state: AgentState):
        docs = self.vector_store.as_retriever(search_kwargs={"k": 8}).invoke(state["question"])
        return {"documents": docs}

    def _legal_expert(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are a Senior Legal Counsel. Analyze the following context for legal implications, "
            "compliance issues, and contractual obligations related to the question.\n"
            "Context: {context}\nQuestion: {question}"
        )
        context = "\n\n".join([d.page_content for d in state["documents"]])
        res = self.llm.invoke(prompt.format(context=context, question=state["question"]))
        return {"legal_opinion": res.content}

    def _financial_expert(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are a Senior Financial Analyst. Extract and analyze financial figures, "
            "market trends, and fiscal health indicators from the context.\n"
            "Context: {context}\nQuestion: {question}"
        )
        context = "\n\n".join([d.page_content for d in state["documents"]])
        res = self.llm.invoke(prompt.format(context=context, question=state["question"]))
        return {"financial_analysis": res.content}

    def _market_researcher(self, state: AgentState):
        # In a real empire edition, we'd use a search tool here. 
        # For now, we simulate high-level market intelligence reasoning.
        prompt = ChatPromptTemplate.from_template(
            "You are a Market Intelligence Expert. Based on the documents and the question, "
            "provide external market context and regulatory environment analysis.\n"
            "Context: {context}\nQuestion: {question}"
        )
        context = "\n\n".join([d.page_content for d in state["documents"]])
        res = self.llm.invoke(prompt.format(context=context, question=state["question"]))
        return {"market_intelligence": res.content}

    def _risk_manager(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are a Chief Risk Officer. Review the legal opinion and financial analysis. "
            "Identify hidden risks, potential liabilities, and adversarial scenarios.\n"
            "Legal: {legal}\nFinancial: {financial}\nQuestion: {question}"
        )
        res = self.llm.invoke(prompt.format(
            legal=state.get("legal_opinion", ""),
            financial=state.get("financial_analysis", ""),
            question=state["question"]
        ))
        return {"risk_assessment": res.content}

    def _aggregator(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are the Lead Strategist. Synthesize the findings from the Legal, Financial, Market, and Risk experts "
            "into a single, incomparable executive summary. \n"
            "If figures exist, provide a chart JSON: {\"type\": \"bar|line\", \"title\": \"...\", \"labels\": [], \"values\": []}\n"
            "Legal: {legal}\nFinancial: {financial}\nMarket: {market}\nRisk: {risk}\nQuestion: {question}"
        )
        res = self.llm.invoke(prompt.format(
            legal=state["legal_opinion"],
            financial=state["financial_analysis"],
            market=state["market_intelligence"],
            risk=state["risk_assessment"],
            question=state["question"]
        ))
        
        # Chart extraction logic
        chart_data = None
        try:
            match = re.search(r'\{.*"values".*\}', res.content, re.DOTALL)
            if match:
                chart_data = json.loads(match.group())
                clean_content = res.content.replace(match.group(), "").strip()
            else:
                clean_content = res.content
        except:
            clean_content = res.content

        return {"final_consensus": clean_content, "chart_data": chart_data}

    def query(self, question: str) -> Dict:
        if self.vector_store is None:
            return {"answer": "Please upload documents first.", "chart": None}
        
        inputs = {"question": question, "steps": []}
        result = self.workflow.invoke(inputs)
        
        # Combine expert opinions into a detailed report
        full_report = f"### 🛡️ Legal Perspective\n{result['legal_opinion']}\n\n" \
                      f"### 📊 Financial Analysis\n{result['financial_analysis']}\n\n" \
                      f"### 🌐 Market Intelligence\n{result['market_intelligence']}\n\n" \
                      f"### ⚠️ Risk Assessment\n{result['risk_assessment']}\n\n" \
                      f"### 🏛️ Executive Consensus\n{result['final_consensus']}"
        
        return {"answer": full_report, "chart": result.get("chart_data")}

    def reset(self):
        self.vector_store = None
