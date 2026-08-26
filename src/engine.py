"""
FinLegal-Chat Ultimate - AI Engine v5.0
Multi-agent reasoning system with LangGraph for legal, financial, and market analysis.
"""

import os
import re
import json
import logging
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.vectorstores import FAISS
from langgraph.graph import StateGraph, END
from src.automation import DocumentAutomator

logger = logging.getLogger(__name__)


class AgentState(dict):
    """State container for the multi-agent workflow."""
    question: str
    documents: List[Document]
    legal_opinion: str
    financial_analysis: str
    risk_assessment: str
    market_intelligence: str
    final_consensus: str
    chart_data: Optional[Dict]
    language: str
    agent_thinking: Dict[str, str]
    errors: List[str]


class FinLegalUltimateEngine:
    """
    Commercial-grade multi-agent AI engine for legal & financial analysis.
    
    Architecture:
    - Retrieve -> [Legal Expert, Financial Expert, Market Analyst] (parallel)
    - -> Risk Manager -> Aggregator -> Final Output
    """

    def __init__(
        self,
        mode: str = "openai",
        local_url: str = "http://localhost:11434",
        local_model: str = "llama3",
        openai_model: str = "gpt-4o",
        api_key: str = None,
        chunk_size: int = 2000,
        chunk_overlap: int = 300,
        retrieval_k: int = 10,
        temperature: float = 0.0,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ):
        self.mode = mode
        self.on_progress = on_progress
        self.vector_store: Optional[FAISS] = None
        self.ingested_documents: List[str] = []
        self._is_processing = False

        # Initialize LLM and embeddings based on mode
        if mode == "openai":
            key = api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI API key is required for cloud mode.")
            self.embeddings = OpenAIEmbeddings(openai_api_key=key)
            self.llm = ChatOpenAI(
                model_name=openai_model,
                temperature=temperature,
                openai_api_key=key,
            )
        else:
            self.embeddings = OllamaEmbeddings(base_url=local_url, model=local_model)
            self.llm = ChatOllama(base_url=local_url, model=local_model, temperature=temperature)

        self.automator = DocumentAutomator()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieval_k = retrieval_k

        self._progress("Engine initialized", 0.0)

    def _progress(self, message: str, pct: float):
        """Report progress to the UI."""
        if self.on_progress:
            try:
                self.on_progress(message, pct)
            except Exception:
                pass
        logger.info(f"[Progress {pct*100:.0f}%] {message}")

    def reconfigure(self, **kwargs):
        """Reconfigure engine parameters. Returns a new engine instance."""
        self._progress("Reconfiguring engine...", 0.0)
        new_engine = FinLegalUltimateEngine(**kwargs, on_progress=self.on_progress)
        # Migrate existing vector store if documents were ingested
        if self.vector_store is not None:
            new_engine.vector_store = self.vector_store
            new_engine.ingested_documents = list(self.ingested_documents)
        new_engine._progress("Engine reconfigured", 1.0)
        return new_engine

    # --- Document Ingestion ---

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a document with high fidelity parsing.
        Returns metadata about the ingestion process.
        """
        self._progress(f"Ingesting: {os.path.basename(file_path)}", 0.1)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext in (".docx", ".doc"):
                try:
                    loader = Docx2txtLoader(file_path)
                except Exception:
                    loader = UnstructuredWordDocumentLoader(file_path)
            elif ext in (".txt", ".md"):
                loader = TextLoader(file_path, encoding="utf-8")
            elif ext in (".csv", ".tsv"):
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                loader = TextLoader(file_path, encoding="utf-8")

            documents = loader.load()
            self._progress("Parsing document structure...", 0.3)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )
            texts = text_splitter.split_documents(documents)
            self._progress(f"Split into {len(texts)} chunks...", 0.5)

            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(texts, self.embeddings)
            else:
                self.vector_store.add_documents(texts)

            self.ingested_documents.append(file_path)
            self._progress(f"Document ingested successfully", 1.0)

            return {
                "success": True,
                "filename": os.path.basename(file_path),
                "chunks": len(texts),
                "total_documents": len(self.ingested_documents),
                "file_type": ext,
            }
        except Exception as e:
            self._progress(f"Ingestion failed: {str(e)}", 0.0)
            logger.error(f"Document ingestion error: {e}", exc_info=True)
            raise

    def remove_document(self, file_path: str):
        """Remove a document from the ingested list (full re-ingest required for vector store)."""
        if file_path in self.ingested_documents:
            self.ingested_documents.remove(file_path)

    def reingest_all(self, file_paths: List[str]):
        """Re-ingest all documents to rebuild the vector store."""
        self.vector_store = None
        self._progress("Rebuilding vector store...", 0.0)
        total = len(file_paths)
        for i, fp in enumerate(file_paths):
            try:
                self.ingest_document(fp)
                self._progress(f"Re-ingesting {i+1}/{total}...", (i + 1) / total)
            except Exception as e:
                logger.error(f"Failed to re-ingest {fp}: {e}")
        self._progress("Vector store rebuilt", 1.0)

    # --- Workflow Definition ---

    def _build_workflow(self) -> StateGraph:
        """Build the multi-agent LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Register nodes
        workflow.add_node("retrieve", self._node_retrieve)
        workflow.add_node("legal_expert", self._node_legal_expert)
        workflow.add_node("financial_expert", self._node_financial_expert)
        workflow.add_node("market_researcher", self._node_market_researcher)
        workflow.add_node("risk_manager", self._node_risk_manager)
        workflow.add_node("aggregator", self._node_aggregator)

        # Define edges: fan-out from retrieve to 3 parallel experts
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "legal_expert")
        workflow.add_edge("retrieve", "financial_expert")
        workflow.add_edge("retrieve", "market_researcher")

        # All experts converge to risk manager
        workflow.add_edge("legal_expert", "risk_manager")
        workflow.add_edge("financial_expert", "risk_manager")
        workflow.add_edge("market_researcher", "risk_manager")

        # Risk manager to final aggregator
        workflow.add_edge("risk_manager", "aggregator")
        workflow.add_edge("aggregator", END)

        return workflow

    # --- Agent Nodes ---

    def _node_retrieve(self, state: AgentState) -> Dict:
        """Retrieve relevant documents from the vector store."""
        self._progress("Searching knowledge base...", 0.05)
        
        if self.vector_store is None:
            return {
                "documents": [],
                "errors": ["No documents have been uploaded yet. Please upload documents first."],
            }

        try:
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": self.retrieval_k}
            )
            docs = retriever.invoke(state["question"])
            self._progress(f"Found {len(docs)} relevant chunks", 0.15)
            return {
                "documents": docs,
                "errors": [],
            }
        except Exception as e:
            self._progress(f"Retrieval error: {str(e)}", 0.1)
            return {"documents": [], "errors": [str(e)]}

    def _node_legal_expert(self, state: AgentState) -> Dict:
        """Legal analysis expert agent."""
        self._progress("Legal Expert analyzing...", 0.2)
        context = self._extract_context(state["documents"])

        prompt = ChatPromptTemplate.from_template(
            """You are an elite Legal AI Consultant with expertise in international law, 
contracts, compliance, and regulatory frameworks. You analyze documents with 
meticulous precision.

INSTRUCTIONS:
- Analyze the provided context thoroughly in its ORIGINAL language
- Identify all legal implications, obligations, and potential risks
- Reference specific clauses, articles, or provisions when possible
- Consider jurisdiction-specific nuances
- Provide actionable legal recommendations

CONTEXT:
{context}

QUESTION:
{question}

Provide a comprehensive legal analysis:"""
        )

        try:
            response = self.llm.invoke(
                prompt.format(context=context, question=state["question"])
            )
            self._progress("Legal Expert completed", 0.35)
            return {
                "legal_opinion": response.content,
                "agent_thinking": {**state.get("agent_thinking", {}), "legal": "completed"},
            }
        except Exception as e:
            return {"legal_opinion": f"Legal analysis error: {str(e)}", "errors": state.get("errors", []) + [str(e)]}

    def _node_financial_expert(self, state: AgentState) -> Dict:
        """Financial analysis expert agent."""
        self._progress("Financial Expert analyzing...", 0.25)
        context = self._extract_context(state["documents"])

        prompt = ChatPromptTemplate.from_template(
            """You are a Senior Financial Strategist and CPA with deep expertise in 
fiscal analysis, financial modeling, and regulatory compliance.

INSTRUCTIONS:
- Extract all financial data, figures, and metrics from the context
- Perform trend analysis and identify patterns
- Assess financial health indicators and KPIs
- Identify potential financial risks and opportunities
- Provide specific numerical insights where data is available

CONTEXT:
{context}

QUESTION:
{question}

Provide a comprehensive financial analysis:"""
        )

        try:
            response = self.llm.invoke(
                prompt.format(context=context, question=state["question"])
            )
            self._progress("Financial Expert completed", 0.4)
            return {
                "financial_analysis": response.content,
                "agent_thinking": {**state.get("agent_thinking", {}), "financial": "completed"},
            }
        except Exception as e:
            return {"financial_analysis": f"Financial analysis error: {str(e)}", "errors": state.get("errors", []) + [str(e)]}

    def _node_market_researcher(self, state: AgentState) -> Dict:
        """Market intelligence expert agent."""
        self._progress("Market Analyst researching...", 0.3)
        context = self._extract_context(state["documents"])

        prompt = ChatPromptTemplate.from_template(
            """You are a Global Market Intelligence Analyst with expertise in 
market trends, competitive analysis, and regulatory environments.

INSTRUCTIONS:
- Analyze market positioning and competitive landscape
- Identify regulatory changes and their potential impact
- Evaluate market risks and opportunities
- Consider geopolitical and macroeconomic factors
- Provide forward-looking market insights

CONTEXT:
{context}

QUESTION:
{question}

Provide comprehensive market intelligence:"""
        )

        try:
            response = self.llm.invoke(
                prompt.format(context=context, question=state["question"])
            )
            self._progress("Market Analyst completed", 0.45)
            return {
                "market_intelligence": response.content,
                "agent_thinking": {**state.get("agent_thinking", {}), "market": "completed"},
            }
        except Exception as e:
            return {"market_intelligence": f"Market analysis error: {str(e)}", "errors": state.get("errors", []) + [str(e)]}

    def _node_risk_manager(self, state: AgentState) -> Dict:
        """Risk assessment and mitigation expert."""
        self._progress("Risk Manager assessing...", 0.55)

        prompt = ChatPromptTemplate.from_template(
            """You are a Chief Risk Officer (CRO) with expertise in identifying, 
quantifying, and mitigating risks across legal, financial, and market domains.

INSTRUCTIONS:
- Synthesize insights from all expert analyses
- Identify critical risk factors and their interdependencies
- Quantify risk levels (High/Medium/Low) for each category
- Provide specific mitigation strategies for each identified risk
- Highlight any hidden or cascading risks
- Recommend risk monitoring approaches

LEGAL ANALYSIS:
{legal}

FINANCIAL ANALYSIS:
{financial}

MARKET INTELLIGENCE:
{market}

Provide a comprehensive risk assessment:"""
        )

        try:
            response = self.llm.invoke(
                prompt.format(
                    legal=state.get("legal_opinion", "Not available"),
                    financial=state.get("financial_analysis", "Not available"),
                    market=state.get("market_intelligence", "Not available"),
                )
            )
            self._progress("Risk Manager completed", 0.7)
            return {
                "risk_assessment": response.content,
                "agent_thinking": {**state.get("agent_thinking", {}), "risk": "completed"},
            }
        except Exception as e:
            return {"risk_assessment": f"Risk assessment error: {str(e)}", "errors": state.get("errors", []) + [str(e)]}

    def _node_aggregator(self, state: AgentState) -> Dict:
        """Final synthesis agent that produces the executive report."""
        self._progress("Synthesizing final report...", 0.8)

        prompt = ChatPromptTemplate.from_template(
            """You are the Ultimate AI Strategist - the final decision synthesizer. 
Your role is to combine all expert analyses into a coherent, actionable 
executive report.

CRITICAL RULES:
1. Detect the user's language from the question and respond in the SAME language
2. Structure the report with clear sections and professional formatting
3. Prioritize actionable insights over theoretical analysis
4. Include specific data points and citations where available
5. Use markdown formatting for headers, lists, and emphasis
6. If financial data is present, include a chart specification as JSON:
   {{"type": "bar" or "line", "title": "Chart Title", "labels": ["A","B"], "values": [10,20]}}
   Place this at the END of your response, clearly separated
7. Provide a clear executive summary at the top

LEGAL CORE:
{legal}

FINANCIAL MATRIX:
{financial}

MARKET INTELLIGENCE:
{market}

RISK ASSESSMENT:
{risk}

ORIGINAL QUESTION:
{question}

PRODUCE THE SUPREME EXECUTIVE REPORT:"""
        )

        try:
            response = self.llm.invoke(
                prompt.format(
                    legal=state.get("legal_opinion", ""),
                    financial=state.get("financial_analysis", ""),
                    market=state.get("market_intelligence", ""),
                    risk=state.get("risk_assessment", ""),
                    question=state["question"],
                )
            )
            content = response.content
            chart_data = None

            # Extract chart JSON if present
            try:
                match = re.search(
                    r'\{[^{}]*"type"\s*:\s*"(?:bar|line)"[^{}]*"values"[^{}]*\}',
                    content,
                    re.DOTALL,
                )
                if match:
                    chart_data = json.loads(match.group())
                    content = content.replace(match.group(), "").strip()
                    # Clean up any trailing separators
                    content = re.sub(r'\n{3,}', '\n\n', content).strip()
            except (json.JSONDecodeError, AttributeError):
                pass

            self._progress("Report synthesized successfully", 0.95)
            return {
                "final_consensus": content,
                "chart_data": chart_data,
                "agent_thinking": {**state.get("agent_thinking", {}), "aggregator": "completed"},
            }
        except Exception as e:
            return {
                "final_consensus": f"Synthesis error: {str(e)}",
                "chart_data": None,
                "errors": state.get("errors", []) + [str(e)],
            }

    # --- Query Execution ---

    def query(self, question: str, session_id: str = None, reports_dir: str = "reports") -> Dict:
        """
        Execute a full multi-agent query pipeline.
        Returns a dict with answer, chart_data, reports, and metadata.
        """
        if self._is_processing:
            return {"answer": "A query is already being processed. Please wait.", "chart": None}
        
        self._is_processing = True
        
        try:
            if self.vector_store is None:
                return {
                    "answer": "Please upload documents first to build the knowledge base. "
                             "The AI engine requires documents to analyze.",
                    "chart": None,
                    "reports": {},
                    "sources": [],
                }

            self._progress("Building analysis pipeline...", 0.0)
            workflow = self._build_workflow().compile()

            inputs: AgentState = {
                "question": question,
                "documents": [],
                "legal_opinion": "",
                "financial_analysis": "",
                "risk_assessment": "",
                "market_intelligence": "",
                "final_consensus": "",
                "chart_data": None,
                "language": "",
                "agent_thinking": {},
                "errors": [],
            }

            result = workflow.invoke(inputs)

            # Build comprehensive report
            sections = []
            if result.get("legal_opinion"):
                sections.append(f"### Legal Analysis\n{result['legal_opinion']}")
            if result.get("financial_analysis"):
                sections.append(f"### Financial Analysis\n{result['financial_analysis']}")
            if result.get("market_intelligence"):
                sections.append(f"### Market Intelligence\n{result['market_intelligence']}")
            if result.get("risk_assessment"):
                sections.append(f"### Risk Assessment\n{result['risk_assessment']}")
            if result.get("final_consensus"):
                sections.append(f"### Executive Summary\n{result['final_consensus']}")

            full_report = "\n\n---\n\n".join(sections)
            chart_data = result.get("chart_data")
            errors = result.get("errors", [])

            # Generate automated reports
            report_files = {}
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            try:
                report_data = {
                    "Legal Analysis": result.get("legal_opinion", ""),
                    "Financial Analysis": result.get("financial_analysis", ""),
                    "Market Intelligence": result.get("market_intelligence", ""),
                    "Risk Assessment": result.get("risk_assessment", ""),
                    "Executive Summary": result.get("final_consensus", ""),
                }
                word_path = os.path.join(reports_dir, f"Analysis_{timestamp}.docx")
                self.automator.create_legal_report(
                    f"FinLegal Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    report_data,
                    word_path,
                )
                report_files["word"] = word_path
            except Exception as e:
                logger.error(f"Word report generation failed: {e}")

            if chart_data:
                try:
                    excel_path = os.path.join(reports_dir, f"Data_{timestamp}.xlsx")
                    self.automator.create_financial_spreadsheet(chart_data, excel_path)
                    report_files["excel"] = excel_path
                except Exception as e:
                    logger.error(f"Excel report generation failed: {e}")

            self._progress("Analysis complete", 1.0)

            return {
                "answer": full_report,
                "chart": chart_data,
                "reports": report_files,
                "errors": errors,
                "agents_completed": result.get("agent_thinking", {}),
            }
        except Exception as e:
            self._progress(f"Query failed: {str(e)}", 0.0)
            logger.error(f"Query execution error: {e}", exc_info=True)
            return {
                "answer": f"An error occurred during analysis: {str(e)}",
                "chart": None,
                "reports": {},
                "errors": [str(e)],
            }
        finally:
            self._is_processing = False

    # --- Utilities ---

    @staticmethod
    def _extract_context(documents: List[Document]) -> str:
        """Extract text content from Document objects."""
        if not documents:
            return "No relevant documents found in the knowledge base."
        parts = []
        for doc in documents:
            text = doc.page_content.strip()
            if text:
                source = doc.metadata.get("source", "")
                if source:
                    parts.append(f"[Source: {os.path.basename(source)}]\n{text}")
                else:
                    parts.append(text)
        return "\n\n---\n\n".join(parts)

    def is_ready(self) -> bool:
        """Check if the engine is ready to process queries."""
        return self.vector_store is not None

    def get_document_count(self) -> int:
        """Return the number of ingested documents."""
        return len(self.ingested_documents)

    def reset(self):
        """Reset the engine, clearing the vector store."""
        self.vector_store = None
        self.ingested_documents = []
        self._is_processing = False
        self._progress("Engine reset", 0.0)

    @property
    def is_processing(self) -> bool:
        return self._is_processing
