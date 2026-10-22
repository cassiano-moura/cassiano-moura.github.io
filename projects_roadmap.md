# Mapa Estratégico dos Projetos Práticos (Portfólio de Elite)

**Candidato:** Cassiano Moura  
**Foco:** Cloud Support Associate / Cloud Operations (AWS) & Enterprise Technical Support Engineer (N2/N3)

---

## 🎯 Filosofia de Portfólio: Profundidade sobre Volume
> **Nota Estratégica:** Gestores de engenharia e Tech Leads **não contratam por quantidade de repositórios "hello world"**, mas por **projetos profundos, resilientes e orientados a produção**.
> Uma esteira coesa de 5 a 6 projetos documentados de ponta a ponta com Terraform, diagramas de rede, observabilidade, FinOps e runbooks de troubleshooting coloca o candidato no percentil superior de qualquer processo seletivo.

---

## Tabela Resumo dos Projetos

| # | Projeto | O que demonstra ao Recrutador / Gestor | Stack Tecnológica | Status |
| :-: | :--- | :--- | :--- | :-: |
| **1** | **Arquitetura Multi-Tier Segura na AWS** | Criação de rede corporativa isolada (VPC, Subnets em 2 AZs, Internet Gateway, NAT Gateway e Security Groups com princípio do menor privilégio). Computação com Auto Scaling EC2 e banco Multi-AZ RDS MySQL. Inclui Playbook de Troubleshooting N2/N3 com RCA de erros 502/504 e conexões DB. | Terraform, AWS VPC, Subnets, ALB, ASG, RDS MySQL, IAM | **Concluído & Documentado** |
| **2** | **Pipeline de Resposta a Incidentes (CloudOps)** | Monitoramento de métricas corporativas de infraestrutura. Alarme de CPU/Disco no CloudWatch que dispara notificação via Amazon SNS e aciona uma função AWS Lambda em Python para auto-remediação (reinício seguro de serviços e purga de cache/logs via AWS Systems Manager) com alerta aos engenheiros. | AWS CloudWatch, Amazon SNS, AWS Lambda (Python 3.12), AWS Systems Manager, Terraform | **Concluído & Testado** |
| **3** | **Troubleshooting de APIs e Observabilidade** | Resolução profunda de falhas de microsserviços. Estruturação de logs de API em formato JSON estruturado, suíte Postman simulando tráfego real com códigos HTTP (200, 201, 400, 401, 404, 500, 504), e queries analíticas no Splunk (SPL) e Grafana para isolamento de causa raiz (RCA) e taxa de erro. | Docker, Docker Compose, Python, Postman, Splunk (SPL), Grafana | **Concluído & Documentado** |
| **4** | **Acesso Remoto Zero-Trust & Governança** | Eliminação completa de portas de gerenciamento abertas (Porta 22 SSH fechada). Gestão de acesso via AWS Systems Manager Session Manager, trilhas de auditoria criptografadas no Amazon S3 (KMS) e integração com Microsoft Entra ID (Azure AD). | AWS Systems Manager (SSM), Microsoft Entra ID, Amazon S3 KMS, Terraform, IAM | **Concluído & Documentado** |
| **5** | **Centro de Operações Multi-Cloud & Incidentes (AWS • Azure • OCI)** | Sustentação de ambientes multi-cloud para turno noturno de operações/NOC. Automação de health check sintético em Python, runbooks de incidentes críticos (saturação de disco/inodes, ALB 502/504, falha de backup Commvault/AWS), template de GMUD (ITIL v4) com rollback e passagem de turno estruturada no ITSM (Freshservice). | Python 3.12, AWS CLI, OCI, Azure, ITIL v4 (GMUD), Zabbix, Freshservice | **Concluído & Documentado** |
| **6** | **CI/CD Seguro de Terraform com FinOps & Security Gate** | Esteira automatizada de validação de IaC via GitHub Actions. State locking com DynamoDB e S3 backend remoto. Análise estática com TFLint, auditoria de segurança com Trivy/tfsec e FinOps com Infracost. | GitHub Actions, Terraform, DynamoDB, TFLint, Trivy/tfsec, Infracost, AWS IAM OIDC | **Em Implementação** |

---

## Detalhamento dos Novos Projetos (Roadmap de Alta Empregabilidade)

### Projeto 5: Pipeline CI/CD Seguro de Terraform com FinOps & Security Gate
* **Cenário Real do Mercado:** As empresas têm receio de adotar Terraform em times múltiplos por três riscos:
  1. Concorrência: dois engenheiros aplicando mudanças simultâneas e corrompendo o arquivo `terraform.tfstate`.
  2. Riscos de Segurança: commits acidentais de Security Groups abertos para a internet (`0.0.0.0/0`) ou credenciais IAM expostas.
  3. Custo Surpresa: um pull request aprovado que cria instâncias superdimensionadas ou múltiplos NAT Gateways, dobrando a fatura da AWS.
* **Solução Implementada:**
  - Backend S3 com criptografia KMS e **DynamoDB State Locking**.
  - Pipeline no **GitHub Actions** acionado a cada Pull Request usando autenticação segura sem chaves estáticas (**AWS IAM OIDC**).
  - Quality Gate com 3 etapas automáticas:
    1. `terraform fmt` e `tflint` (qualidade de código).
    2. `trivy config` / `tfsec` (varredura de compliance e vulnerabilidades).
    3. `infracost breakdown` (comentário automático no PR informando a variação exata de custo em dólares/mês).

---

### Projeto 6: Plataforma de Observabilidade Centralizada & APM com Grafana Cloud
* **Cenário Real do Mercado:** Suporte Enterprise e SREs não podem depender de avisos de clientes para saber que a API está lenta. É necessário detectar degradação antes que o cliente sinta.
* **Solução Implementada:**
  - Container Docker rodando aplicação instrumentada com métricas Prometheus.
  - **AWS CloudWatch Prometheus Exporter** consolidando métricas de ALB (latência target, HTTP 5xx) e RDS (CPU, conexões ativas e IOPs).
  - Dashboards executivos e operacionais no **Grafana Cloud Free Tier**.
  - Roteamento inteligente de alertas via **Alertmanager** para canais de operação com limiares baseados em percentis (latência p95 > 800ms por mais de 3 minutos).
