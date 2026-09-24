# Mapa Estratégico dos Projetos Práticos (Portfólio de Elite)

**Candidato:** Cassiano Moura  
**Objetivo:** Contratação acelerada para vagas nacionais e internacionais em:
1. **Cloud Support Associate / Cloud Operations (AWS)**
2. **Technical Support Engineer (Enterprise N2/N3, Application Support, APIs e Observabilidade)**

---

## Tabela Resumo dos Projetos

| # | Projeto | O que demonstra ao Recrutador / Gestor | Stack Tecnológica | Status |
| :-: | :--- | :--- | :--- | :-: |
| **1** | **Arquitetura Multi-Tier Segura na AWS** | Criação de rede corporativa isolada (VPC, Subnets em 2 AZs, Internet Gateway, NAT Gateway e Security Groups com princípio do menor privilégio). Computação com Auto Scaling EC2 e banco Multi-AZ RDS MySQL. Inclui Playbook de Troubleshooting N2/N3 com RCA de erros 502/504 e conexões DB. | Terraform, AWS VPC, Subnets, ALB, ASG, RDS MySQL, IAM | **Concluído & Documentado** |
| **2** | **Pipeline de Resposta a Incidentes (CloudOps)** | Monitoramento de métricas corporativas de infraestrutura. Alarme de CPU/Disco no CloudWatch que dispara notificação via Amazon SNS e aciona uma função AWS Lambda em Python para auto-remediação (reinício seguro de serviços e purga de cache/logs via AWS Systems Manager) com alerta aos engenheiros. | AWS CloudWatch, Amazon SNS, AWS Lambda (Python 3.12), AWS Systems Manager, Terraform | **Concluído & Testado** |
| **3** | **Troubleshooting de APIs e Observabilidade** | Resolução profunda de falhas de microsserviços. Estruturação de logs de API em formato JSON estruturado, suíte Postman simulando tráfego real com códigos HTTP (200, 201, 400, 401, 404, 500, 504), e queries analíticas no Splunk (SPL) e Grafana para isolamento de causa raiz (RCA) e taxa de erro. | Docker, Docker Compose, Python, Postman, Splunk (SPL), Grafana | **Concluído & Documentado** |
| **4** | **Acesso Remoto Zero-Trust & Governança** | Eliminação completa de portas de gerenciamento abertas (Porta 22 SSH fechada). Gestão de acesso via AWS Systems Manager Session Manager, trilhas de auditoria criptografadas no Amazon S3 (KMS) e integração com Microsoft Entra ID (Azure AD). | AWS Systems Manager (SSM), Microsoft Entra ID, Amazon S3 KMS, Terraform, IAM | **Concluído & Documentado** |

---

## Backlog / Projetos Adicionais para Evolução Futura

* **Projeto Bônus (Serverless Log Monitor):** `projects/project-2-serverless-log-monitor/` — Filtro de logs e disparos de alertas em tempo real via Lambda.
* **Melhorias Futuras Planejadas:**
  1. Integração contínua via **GitHub Actions** (`terraform-validate.yml`) para rodar linters automáticos em pull requests.
  2. Adição de pipeline de **LocalStack** para quem quiser rodar deploy completo 100% offline.
  3. Dashboard ao vivo no Grafana Cloud Free Tier integrado aos logs do container Docker.
