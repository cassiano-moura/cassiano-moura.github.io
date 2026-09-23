# Splunk & Grafana Observability Runbook: API Error Analysis

**Author:** Cassiano Moura  
**Domain:** Enterprise Application Support (Tier 2 / Tier 3)  
**Scope:** Microservice Structured Logs (`JSON format`)  

---

## 1. Splunk Search Processing Language (SPL) Queries

When investigating Sev-1 / Sev-2 application incidents in **Splunk**, use these pre-built diagnostic queries:

### Query 1: Error Rate Percentage (4xx vs 5xx vs 2xx)
Calculates real-time health ratios over 5-minute spans:
```spl
index="production-apis" service="order-management-microservice"
| eval status_type=case(
    status_code>=200 AND status_code<300, "2xx_Success",
    status_code>=400 AND status_code<500, "4xx_Client_Error",
    status_code>=500, "5xx_Server_Failure"
)
| timechart span=5m count by status_type
```

### Query 2: Top Failing Endpoints by 5xx Errors with Error Trace
Isolates critical backend crashes and database timeouts:
```spl
index="production-apis" status_code>=500
| stats count as failure_count, values(error_message) as sample_errors, values(client_ip) as affected_clients by endpoint, status_code
| sort - failure_count
```

### Query 3: Detecting Authentication Attacks or Expired Token Floods (401/403)
Identifies clients or automated integrations failing authentication:
```spl
index="production-apis" (status_code=401 OR status_code=403)
| stats count as auth_failures, latest(error_message) as latest_reason by client_ip, endpoint
| where auth_failures > 20
| sort - auth_failures
```

---

## 2. Grafana Dashboard Panels & Metric Definitions

If using Grafana (Loki / Prometheus):

### Panel 1: API Status Code Distribution (Donut Chart)
* **LogQL / Query:** `sum by (status_code) (count_over_time({service="order-management-microservice"} [5m]))`
* **Visualization:** Donut Chart with color mappings:
  * Green: 200, 201
  * Yellow/Orange: 400, 401, 404
  * Red: 500, 502, 504

### Panel 2: P95 / P99 Latency Heatmap
* **Query:** `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
* **Alert Trigger:** Alert if P95 latency > 2.0s for 3 consecutive minutes.

### Panel 3: Live Incident Forensic Log Stream
* **Filter:** `{service="order-management-microservice"} | json | status_code >= 400`
* **Fields Displayed:** `timestamp`, `method`, `endpoint`, `status_code`, `client_ip`, `error_message`.
