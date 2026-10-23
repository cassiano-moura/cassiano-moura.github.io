from fastapi import APIRouter, HTTPException, Depends
from app.schemas.agent_schema import ChatRequest, ChatResponse, SalesforceCaseCreate, SalesforceCaseResponse
from app.services.salesforce_service import SalesforceConnector
from app.services.agent_service import EnterpriseSupportAgent

router = APIRouter()

# Dependency singletons
_sf_connector = SalesforceConnector()
_agent_service = EnterpriseSupportAgent(_sf_connector)


def get_agent_service() -> EnterpriseSupportAgent:
    return _agent_service


def get_sf_connector() -> SalesforceConnector:
    return _sf_connector


@router.post("/agent/chat", response_model=ChatResponse, summary="Interact with Enterprise AI Agent")
async def chat_with_agent(
    payload: ChatRequest,
    agent: EnterpriseSupportAgent = Depends(get_agent_service)
):
    """
    Primary endpoint for customer chat. 
    Processes conversation, triggers tool/function calling (Salesforce lookup/case creation),
    applies RAG over engineering runbooks, and evaluates SLA escalation.
    """
    return await agent.process_chat(payload)


@router.post("/salesforce/cases", summary="Directly create a Salesforce Case via API")
async def create_case(
    payload: SalesforceCaseCreate,
    sf: SalesforceConnector = Depends(get_sf_connector)
):
    case = await sf.create_support_case(
        account_email=payload.account_email,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority.value,
        category=payload.category
    )
    return case


@router.get("/salesforce/cases/{case_number}", summary="Retrieve Salesforce Case details")
async def get_case_details(
    case_number: str,
    sf: SalesforceConnector = Depends(get_sf_connector)
):
    case = await sf.get_case_status(case_number)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case #{case_number} not found in Salesforce.")
    return case
