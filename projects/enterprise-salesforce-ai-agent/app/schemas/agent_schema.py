from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class PriorityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CaseStatusEnum(str, Enum):
    NEW = "New"
    IN_PROGRESS = "Working"
    ESCALATED = "Escalated"
    CLOSED = "Closed"


# --- Chat & Agent Schemas ---

class ChatRequest(BaseModel):
    customer_id: str = Field(..., description="Corporate account or customer email identifier", example="customer@acmecorp.com")
    message: str = Field(..., description="Customer inquiry or issue report", example="Our production load balancer is returning 502 errors and we need an urgent case opened.")
    session_id: Optional[str] = Field(None, description="Conversational context session ID")


class ToolExecutionRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    status: str = "success"


class ChatResponse(BaseModel):
    reply: str
    intent_detected: str
    confidence_score: float
    tools_executed: List[ToolExecutionRecord] = []
    escalated_to_human: bool = False
    session_id: str


# --- Salesforce Entity Schemas ---

class SalesforceCaseCreate(BaseModel):
    account_email: str
    subject: str
    description: str
    priority: PriorityEnum = PriorityEnum.MEDIUM
    category: str = "Cloud Infrastructure"


class SalesforceCaseResponse(BaseModel):
    case_number: str
    case_id: str
    account_id: str
    subject: str
    status: CaseStatusEnum
    priority: PriorityEnum
    created_at: str
