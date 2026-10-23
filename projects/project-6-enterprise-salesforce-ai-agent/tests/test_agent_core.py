import unittest
import asyncio
from app.services.salesforce_service import SalesforceConnector
from app.services.agent_service import EnterpriseSupportAgent
from app.schemas.agent_schema import ChatRequest


class TestEnterpriseAIAgent(unittest.TestCase):
    def setUp(self):
        self.sf = SalesforceConnector()
        self.agent = EnterpriseSupportAgent(self.sf)

    def test_salesforce_account_lookup(self):
        account = asyncio.run(self.sf.get_account_by_email("customer@acmecorp.com"))
        self.assertIsNotNone(account)
        self.assertEqual(account["name"], "Acme Global Enterprise")
        self.assertEqual(account["tier"], "Mission Critical Enterprise")

    def test_agent_incident_detection_and_salesforce_case_creation(self):
        req = ChatRequest(
            customer_id="customer@acmecorp.com",
            message="Nossos servidores em produção estão com erro 502 urgente no load balancer!"
        )
        response = asyncio.run(self.agent.process_chat(req))

        self.assertEqual(response.intent_detected, "incident_report")
        self.assertTrue(response.escalated_to_human)
        self.assertIn("Caso #", response.reply)
        self.assertIn("Acme Global Enterprise", response.tools_executed[0].result["name"])

        tool_names = [t.tool_name for t in response.tools_executed]
        self.assertIn("salesforce_lookup_account", tool_names)
        self.assertIn("query_kb_rag", tool_names)
        self.assertIn("salesforce_create_case", tool_names)

    def test_agent_general_inquiry_no_escalation(self):
        req = ChatRequest(
            customer_id="tech@fintechpay.io",
            message="Qual é o procedimento para solicitar nova GMUD?"
        )
        response = asyncio.run(self.agent.process_chat(req))

        self.assertEqual(response.intent_detected, "general_inquiry")
        self.assertFalse(response.escalated_to_human)
        self.assertIn("posso ajudar", response.reply.lower())


if __name__ == "__main__":
    unittest.main()
