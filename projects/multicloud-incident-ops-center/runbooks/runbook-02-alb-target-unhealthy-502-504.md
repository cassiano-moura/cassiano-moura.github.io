# Runbook 02: Falha de Health Check em Load Balancer e Erros HTTP 502/504

**Código do Procedimento:** `RBK-OPS-ALB-02`  
**Escopo:** AWS Application Load Balancer (ALB) / OCI Public Load Balancer / Nginx  
**Severidade do Alerta:** P1 (Crítico - Target Group com 0 instâncias saudáveis) / P2 (Degradação com 50% dos targets falhando)  
**Turno:** Operação Noturna e Sustentação Contínua (NOC / CloudOps)  
**Autor:** Cassiano Moura (Cloud Support Associate / NOC Operations)

---

## 1. Descrição do Incidente & Gatilho
* **Alerta do Monitoramento:** CloudWatch ou Dynatrace dispara:
  - `UnHealthyHostCount >= 1`
  - `HTTPCode_Target_5XX_Count > 15 em janela de 3 minutos`
  - `TargetResponseTime > 3.0s (p95)`
* **Sintoma para o Usuário Final:** Mensagens de navegador: `502 Bad Gateway` ou `504 Gateway Time-out`.

---

## 2. Matriz Diagnóstica: Diferença entre Erro 502 e 504

| Código HTTP | Significado Técnico | Onde está a falha provável? |
| :--- | :--- | :--- |
| **HTTP 502 (Bad Gateway)** | O Load Balancer recebeu uma resposta inválida ou o backend fechou a conexão TCP abruptamente antes de responder (TCP RST). | Aplicação no EC2/Container deu crash, estourou memória (OOM Killer) ou porta da aplicação não está aberta. |
| **HTTP 504 (Gateway Timeout)** | O Load Balancer conectou ao backend, enviou a requisição HTTP, mas a aplicação demorou mais que o `idle_timeout` (ex: 60s) para responder. | Consulta SQL lenta bloqueando a thread, pool de conexões do banco esgotado, ou chamada a API externa com timeout. |

---

## 3. Fluxo de Investigação Operacional no Turno Noturno

### 3.1 Inspeção do Status do Target Group via AWS CLI
```bash
# 1. Identificar o estado exato dos targets registrados
aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/prod-app-tg/abcdef123456"

# Exemplo de retorno indicativo de falha:
# "Target": { "Id": "i-0123456789abcdef0", "Port": 80 },
# "TargetHealth": {
#     "State": "unhealthy",
#     "Reason": "Target.ResponseCodeMismatch",
#     "Description": "Health checks failed with these codes: [404]"
# }
```

### 3.2 Validação Local do Endpoint de Health Check
Acessar a instância via **AWS Systems Manager** e simular o health check internamente:
```bash
# Testar localmente a resposta do endpoint de saúde
curl -Iv http://localhost:80/healthz

# Verificar se o serviço web está escutando na porta correta
sudo ss -tulpn | grep -E ':(80|443|8080|3000)'

# Checar se houve OOM Killer (processo finalizado por falta de RAM)
sudo dmesg -T | grep -i -E '(oom-killer|out of memory)'
```

### 3.3 Verificação de Conectividade e Regras de Security Group
Garantir que a regra de segurança do Security Group da instância permite tráfego de entrada proveniente do Security Group do ALB:
```bash
# Verificar Security Group do Target Group
aws ec2 describe-security-groups --group-ids sg-0123456789abcdef0
```

---

## 4. Ações de Mitigação Imediata

### Cenário A: O endpoint retorna 404 ou formato inesperado
* Se a equipe de desenvolvimento subiu uma release que alterou a rota do health check (ex: de `/health` para `/api/healthz`), abrir **GMUD Emergencial** e atualizar a rota no Target Group:
```bash
aws elbv2 modify-target-group \
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/prod-app-tg/abcdef123456" \
  --health-check-path "/api/healthz"
```

### Cenário B: Instância congelada por saturação de conexões
```bash
# 1. Checar conexões ativas no Linux
netstat -an | grep :80 | wc -l

# 2. Reiniciar serviço suavemente
sudo systemctl restart gunicorn || sudo systemctl restart nginx

# 3. Monitorar Target Group até o estado transicionar para "healthy"
aws elbv2 describe-target-health --target-group-arn <TARGET_GROUP_ARN> --query "TargetHealthDescriptions[*].TargetHealth.State"
```

---

## 5. Passagem de Contexto e Comunicação
* **Atualizar chamado no Freshservice:**
  - *"Alerta de Unhealthy Target Group mitigado às 02:45 UTC. Instância i-0123456789abcdef0 reiniciada após identificação de trava no processo worker do backend. Target retornou ao status Healthy e latência normalizada em 140ms."*
* **Se persistir por mais de 10 minutos com tráfego afetado:** Acionar imediatamente o **Engenheiro de Software de Plantão N3 (Dev/SRE)** conforme matriz de escalonamento.
