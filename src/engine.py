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
from src.automation import DocumentAutomator

# --- Ultimate State Definition ---
class AgentState(TypedDict):
    question: str
    documents: List[str]
    legal_opinion: str
    financial_analysis: str
    risk_assessment: str
    market_intelligence: str
    final_consensus: str
    chart_data: Dict
    language: str
    steps: List[str]

class FinLegalUltimateEngine:
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
        self.workflow = self._build_ultimate_workflow()
        self.automator = DocumentAutomator()

    def ingest_document(self, file_path: str):
        """Ultra-high fidelity ingestion with format detection."""
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""]
        )
        texts = text_splitter.split_documents(documents)
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
        else:
            self.vector_store.add_documents(texts)

    def _build_ultimate_workflow(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("legal_expert", self._legal_expert)
        workflow.add_node("financial_expert", self._financial_expert)
        workflow.add_node("market_researcher", self._market_researcher)
        workflow.add_node("risk_manager", self._risk_manager)
        workflow.add_node("aggregator", self._aggregator)

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
        docs = self.vector_store.as_retriever(search_kwargs={"k": 10}).invoke(state["question"])
        return {"documents": docs}

    def _legal_expert(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are a Supreme Legal AI. Analyze the context in its original language (Persian/English/etc.) "
            "and provide a detailed legal opinion. \nContext: {context}\nQuestion: {question}"
        )
        context = "\n\n".join([d.page_content for d in state["documents"]])
        res = self.llm.invoke(prompt.format(context=context, question=state["question"]))
        return {"legal_opinion": res.content}

    def _financial_expert(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are a Global Financial Strategist. Analyze fiscal data and trends. \nContext: {context}\nQuestion: {question}"
        )
        context = "\n\n".join([d.page_content for d in state["documents"]])
        res = self.llm.invoke(prompt.format(context=context, question=state["question"]))
        return {"financial_analysis": res.content}

    def _market_researcher(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are an Omni-Market Analyst. Evaluate global trends and regulatory shifts. \nContext: {context}\nQuestion: {question}"
        )
        context = "\n\n".join([d.page_content for d in state["documents"]])
        res = self.llm.invoke(prompt.format(context=context, question=state["question"]))
        return {"market_intelligence": res.content}

    def _risk_manager(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are a Master of Risk. Identify all potential threats and adversarial outcomes. \nLegal: {legal}\nFinancial: {financial}\nMarket: {market}"
        )
        res = self.llm.invoke(prompt.format(
            legal=state.get("legal_opinion", ""),
            financial=state.get("financial_analysis", ""),
            market=state.get("market_intelligence", ""),
        ))
        return {"risk_assessment": res.content}

    def _aggregator(self, state: AgentState):
        prompt = ChatPromptTemplate.from_template(
            "You are the Ultimate AI Strategist. Synthesize all findings into a supreme executive report. "
            "Detect the user's language and respond in that language. \n"
            "Include chart JSON if applicable: {\"type\": \"bar|line\", \"title\": \"...\", \"labels\": [], \"values\": []}\n"
            "Legal: {legal}\nFinancial: {financial}\nMarket: {market}\nRisk: {risk}\nQuestion: {question}"
        )
        res = self.llm.invoke(prompt.format(
            legal=state["legal_opinion"],
            financial=state["financial_analysis"],
            market=state["market_intelligence"],
            risk=state["risk_assessment"],
            question=state["question"]
        ))
        
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
        
        full_report = f"### 🛡️ Legal Core\n{result['legal_opinion']}\n\n" \
                      f"### 📊 Financial Matrix\n{result['financial_analysis']}\n\n" \
                      f"### 🌐 Market Intelligence\n{result['market_intelligence']}\n\n" \
                      f"### ⚠️ Risk Mitigation\n{result['risk_assessment']}\n\n" \
                      f"### 🏛️ Supreme Consensus\n{result['final_consensus']}"
        
        # Automation: Generate report files
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        word_path = os.path.join(report_dir, "Ultimate_Analysis.docx")
        self.automator.create_legal_report("Supreme Analysis Report", {
            "Legal Core": result['legal_opinion'],
            "Financial Matrix": result['financial_analysis'],
            "Market Intelligence": result['market_intelligence'],
            "Risk Mitigation": result['risk_assessment'],
            "Supreme Consensus": result['final_consensus']
        }, word_path)

        excel_path = None
        if result.get("chart_data"):
            excel_path = os.path.join(report_dir, "Financial_Data.xlsx")
            self.automator.create_financial_spreadsheet(result["chart_data"], excel_path)
        
        return {
            "answer": full_report, 
            "chart": result.get("chart_data"),
            "reports": {"word": word_path, "excel": excel_path}
        }

    def reset(self):
        self.vector_store = None
