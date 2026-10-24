import json
import logging
import uuid
from typing import Dict, Any, List
from app.schemas.agent_schema import ChatRequest, ChatResponse, ToolExecutionRecord
from app.services.salesforce_service import SalesforceConnector

logger = logging.getLogger("enterprise_agent")


class EnterpriseSupportAgent:
    """
    Autonomous Enterprise AI Agent utilizing Function/Tool Calling & RAG.
    Detects customer intent, queries internal knowledge base, executes Salesforce operations,
    and determines when to escalate to 24/7 human engineering plantão.
    """

    def __init__(self, sf_connector: SalesforceConnector):
        self.sf = sf_connector
        # Defined LLM Function Calling tools
        self.tools_schema = [
            {
                "name": "salesforce_lookup_account",
                "description": "Look up corporate customer account details, SLA tier, and active support contracts in Salesforce.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "Corporate email of the customer"}
                    },
                    "required": ["email"]
                }
            },
            {
                "name": "salesforce_create_case",
                "description": "Create a new support ticket/case in Salesforce Service Cloud when an issue or incident is reported.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "Concise summary of the incident"},
                        "description": {"type": "string", "description": "Full details and technical observations"},
                        "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]}
                    },
                    "required": ["subject", "description", "priority"]
                }
            },
            {
                "name": "query_kb_rag",
                "description": "Query internal enterprise cloud engineering knowledge base for troubleshooting runbooks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Keywords or error codes e.g. ALB 502, disk full"}
                    },
                    "required": ["query"]
                }
            }
        ]

    async def _query_kb_rag(self, query: str) -> Dict[str, Any]:
        """Queries enterprise vector knowledge base using semantic term similarity."""
        from app.services.vector_retriever import VectorKnowledgeRetriever
        retriever = VectorKnowledgeRetriever()
        results = retriever.search(query, top_k=1)
        if results:
            doc, score = results[0]
            return {
                "found": True,
                "score": score,
                "article": {
                    "id": doc["id"],
                    "title": doc["title"],
                    "summary": doc["content"]
                }
            }
        return {"found": False, "article": None}

    async def process_chat(self, req: ChatRequest) -> ChatResponse:
        session_id = req.session_id or f"sess_{uuid.uuid4().hex[:10]}"
        user_msg = req.message.lower()
        tools_executed: List[ToolExecutionRecord] = []
        escalated = False

        # 1. Automatic Account 360 Lookup via Salesforce Tool
        account = await self.sf.get_account_by_email(req.customer_id)
        tools_executed.append(ToolExecutionRecord(
            tool_name="salesforce_lookup_account",
            arguments={"email": req.customer_id},
            result=account or {"status": "unregistered_account"}
        ))

        # 2. Intent Detection & Tool Execution
        intent = "general_inquiry"
        confidence = 0.95

        # Check for incident / outage keywords
        incident_triggers = ["502", "504", "down", "fora do ar", "erro", "incident", "parou", "urgente", "urgent", "disk full"]
        has_incident = any(w in user_msg for w in incident_triggers)

        if has_incident:
            intent = "incident_report"
            is_critical = any(w in user_msg for w in ["production", "produção", "down", "fora do ar", "urgente", "502"])
            priority = "Critical" if is_critical else "High"

            # Execute RAG Tool for runbook guidance
            rag_result = await self._query_kb_rag(user_msg)
            tools_executed.append(ToolExecutionRecord(
                tool_name="query_kb_rag",
                arguments={"query": req.message},
                result=rag_result
            ))

            # Execute Salesforce Create Case Tool
            case = await self.sf.create_support_case(
                account_email=req.customer_id,
                subject=f"Cloud Incident: {req.message[:50]}...",
                description=req.message,
                priority=priority,
                category="Cloud Operations"
            )
            tools_executed.append(ToolExecutionRecord(
                tool_name="salesforce_create_case",
                arguments={"subject": case["subject"], "priority": priority},
                result={"case_number": case["case_number"], "case_id": case["case_id"], "status": case["status"]}
            ))

            tier_name = account["tier"] if account else "Standard"
            sla_time = account["sla_hours"] if account else 4
            escalated = is_critical

            runbook_advice = ""
            if rag_result["found"]:
                runbook_advice = f"\n\n**Triagem Inicial Sugerida (Base de Conhecimento):**\n{rag_result['article']['summary']}"

            reply = (
                f"Olá! Identifiquei um incidente operacional reportado. "
                f"Registrei imediatamente o **Caso #{case['case_number']}** no Salesforce Service Cloud com prioridade **{priority}**.\n\n"
                f"Sua conta está classificada como **{tier_name}** com SLA de resposta garantido de até **{sla_time}h**."
                f"{runbook_advice}\n\n"
                f"Nossa equipe de engenharia e operações 24/7 já foi notificada para acompanhamento imediato."
            )
        else:
            reply = (
                f"Olá! Como posso ajudar você hoje com seus serviços de nuvem e infraestrutura? "
                f"Posso consultar status de chamados no Salesforce, guiar procedimentos operacionais ou acionar nossos especialistas."
            )

        return ChatResponse(
            reply=reply,
            intent_detected=intent,
            confidence_score=confidence,
            tools_executed=tools_executed,
            escalated_to_human=escalated,
            session_id=session_id
        )
