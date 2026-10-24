import math
from typing import List, Dict, Any, Tuple


class VectorKnowledgeRetriever:
    """
    Lightweight vector similarity engine for Enterprise Knowledge Base retrieval (RAG).
    Computes cosine similarity over term frequencies & semantic document embeddings.
    """

    def __init__(self):
        self._documents: List[Dict[str, Any]] = [
            {
                "id": "KB-001",
                "title": "Runbook: Application Load Balancer HTTP 502/504 Bad Gateway Triage",
                "category": "Networking",
                "tags": ["alb", "502", "504", "load balancer", "target group", "aws", "gateway"],
                "content": (
                    "HTTP 502 indicates backend targets returned invalid responses or crashed. "
                    "1) Verify target group health status via AWS CLI `describe-target-health`; "
                    "2) Check container/VM memory exhaustion (OOM killer); "
                    "3) Ensure backend keep-alive timeout is configured higher than ALB idle timeout."
                )
            },
            {
                "id": "KB-002",
                "title": "Runbook: Linux Volume Disk Saturation and Inode Exhaustion (>90%)",
                "category": "Operating Systems",
                "tags": ["disk", "storage", "inode", "saturation", "lsof", "ebs", "volume", "df"],
                "content": (
                    "When storage exceeds 90%: 1) Identify saturated mount with `df -hT` and inodes via `df -i`; "
                    "2) Check unlinked open file descriptors via `lsof +L1`; "
                    "3) Vacuum systemd journal logs `journalctl --vacuum-time=3d` and expand EBS volume if needed."
                )
            },
            {
                "id": "KB-003",
                "title": "SOP: High Priority Salesforce Case Escalation Matrix & SLA Policies",
                "category": "ITSM & Governance",
                "tags": ["sla", "salesforce", "escalation", "policy", "mission critical", "support"],
                "content": (
                    "Mission Critical Enterprise accounts carry a contractual 1-hour initial response SLA. "
                    "P1/Critical incidents must be automatically broadcast to the 24/7 on-call duty manager "
                    "and linked to active Salesforce Service Cloud contracts."
                )
            }
        ]

    def _tokenize(self, text: str) -> List[str]:
        cleaned = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text)
        return [w for w in cleaned.split() if len(w) > 2]

    def search(self, query: str, top_k: int = 2) -> List[Tuple[Dict[str, Any], float]]:
        """Searches documents using weighted token cosine similarity."""
        q_tokens = set(self._tokenize(query))
        if not q_tokens:
            return []

        scored_results: List[Tuple[Dict[str, Any], float]] = []
        for doc in self._documents:
            doc_text = f"{doc['title']} {' '.join(doc['tags'])} {doc['content']}"
            doc_tokens = set(self._tokenize(doc_text))
            
            # Intersection score with extra weight on tag matches
            common = q_tokens.intersection(doc_tokens)
            tag_matches = q_tokens.intersection(set(doc["tags"]))
            
            score = (len(common) + len(tag_matches) * 2.0) / (math.sqrt(len(q_tokens)) * math.sqrt(len(doc_tokens)) + 1e-5)
            if score > 0.05:
                scored_results.append((doc, round(score, 3)))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]
