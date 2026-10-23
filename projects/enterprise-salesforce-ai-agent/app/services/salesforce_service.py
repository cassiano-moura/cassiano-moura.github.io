import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("salesforce_connector")


class SalesforceConnector:
    """
    Simulates / integrates with Salesforce REST API (Service Cloud).
    Provides methods for Case Management, Account 360 lookups, and Entitlement SLA verification.
    """

    def __init__(self, instance_url: str = "https://enterprise-cloudops.my.salesforce.com"):
        self.instance_url = instance_url
        # In-memory mock database for accounts and cases
        self._accounts_db: Dict[str, Dict[str, Any]] = {
            "customer@acmecorp.com": {
                "account_id": "0015g00000XyZ1AAAZ",
                "name": "Acme Global Enterprise",
                "tier": "Mission Critical Enterprise",
                "sla_hours": 1,
                "dedicated_tam": "Sarah Jenkins",
                "active_contracts": ["AWS-Managed-Services-24x7", "OCI-Core-SLA"]
            },
            "tech@fintechpay.io": {
                "account_id": "0015g00000AbC2BBBZ",
                "name": "FintechPay Global",
                "tier": "Business Support",
                "sla_hours": 4,
                "dedicated_tam": "Carlos Mendez",
                "active_contracts": ["Azure-CloudOps-Standard"]
            }
        }
        self._cases_db: List[Dict[str, Any]] = []

    async def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Queries Salesforce Account & Contact sObjects by email."""
        logger.info(f"[Salesforce SOQL] Querying Account for contact: {email}")
        return self._accounts_db.get(email.lower())

    async def create_support_case(
        self,
        account_email: str,
        subject: str,
        description: str,
        priority: str = "Medium",
        category: str = "Cloud Operations"
    ) -> Dict[str, Any]:
        """Creates a new Case sObject in Salesforce Service Cloud."""
        account = await self.get_account_by_email(account_email)
        account_id = account["account_id"] if account else "001000000000DEFAULT"
        account_name = account["name"] if account else "Unregistered Account"

        case_id = f"500{uuid.uuid4().hex[:15].upper()}"
        case_number = f"00{len(self._cases_db) + 4021}"
        now_iso = datetime.now(timezone.utc).isoformat()

        case_record = {
            "case_id": case_id,
            "case_number": case_number,
            "account_id": account_id,
            "account_name": account_name,
            "contact_email": account_email,
            "subject": subject,
            "description": description,
            "priority": priority,
            "category": category,
            "status": "New",
            "created_date": now_iso
        }
        self._cases_db.append(case_record)
        logger.info(f"[Salesforce REST] Created Case #{case_number} for {account_name} (Priority: {priority})")
        return case_record

    async def get_case_status(self, case_number: str) -> Optional[Dict[str, Any]]:
        """Queries Case sObject status and updates by CaseNumber."""
        for c in self._cases_db:
            if c["case_number"] == case_number:
                return c
        return None
