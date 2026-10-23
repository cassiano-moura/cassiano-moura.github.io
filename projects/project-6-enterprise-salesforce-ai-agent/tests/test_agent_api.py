import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Enterprise Salesforce AI Support Agent" in data["app"]


@pytest.mark.asyncio
async def test_agent_chat_general_inquiry():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/agent/chat", json={
            "customer_id": "tech@fintechpay.io",
            "message": "Qual é o horário de atendimento do suporte?"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["intent_detected"] == "general_inquiry"
    assert data["escalated_to_human"] is False
    assert len(data["tools_executed"]) >= 1
    assert data["tools_executed"][0]["tool_name"] == "salesforce_lookup_account"


@pytest.mark.asyncio
async def test_agent_chat_incident_triggers_salesforce_case_and_rag():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/agent/chat", json={
            "customer_id": "customer@acmecorp.com",
            "message": "Nossos servidores em produção estão com erro 502 urgente no load balancer!"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["intent_detected"] == "incident_report"
    assert data["escalated_to_human"] is True
    
    tool_names = [t["tool_name"] for t in data["tools_executed"]]
    assert "salesforce_lookup_account" in tool_names
    assert "query_kb_rag" in tool_names
    assert "salesforce_create_case" in tool_names
    assert "Caso #00" in data["reply"]
