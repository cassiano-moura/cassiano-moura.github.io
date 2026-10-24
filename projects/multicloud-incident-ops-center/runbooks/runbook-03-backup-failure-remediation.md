# Runbook 03: Falha em Rotinas de Backup & Snapshots Multi-Cloud (Commvault / AWS Backup / OCI)

**Código do Procedimento:** `RBK-OPS-BKP-03`  
**Escopo:** Ferramentas Enterprise de Backup (Commvault, AWS Backup, OCI Block Volume Backups)  
**Severidade do Alerta:** P2 (Major - Backup Noturno de Banco de Dados ou VM Falhou)  
**Turno:** Operação Noturna (23h às 08h) — Janela de Backup Crítica  
**Autor:** Cassiano Moura (Cloud Support Associate / NOC Operations)

---

## 1. Contexto Operacional & Janela Noturna
As rotinas corporativas de cópia de segurança (backups completos e incrementais) são executadas tipicamente entre **01:00h e 04:30h**, exatamente no turno noturno de operações, para minimizar o impacto de I/O em bancos de dados em produção.

* **Alerta do Monitoramento:** Alarme disparado no Console Commvault / AWS CloudWatch:
  - `Job ID #98412 Status: FAILED (Error Code: 39:245 - Snapshot Creation Timeout)`
  - `AWS Backup Job State: FAILED (Reason: Insufficient IAM permissions or volume in modifying state)`

---

## 2. Investigação da Causa Raiz (RCA Preliminar)

### 2.1 Inspeção do Job no AWS Backup / CLI
```bash
# Listar jobs de backup com falha nas últimas 6 horas
aws backup list-backup-jobs \
  --by-state FAILED \
  --by-created-after $(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ)

# Detalhar a mensagem de erro específica do job
aws backup describe-backup-job \
  --backup-job-id "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
```

### 2.2 Diagnóstico em Ambientes Commvault
1. Acessar o **Commvault Command Center**.
2. Navegar em: **Jobs** > Selecionar o JobID com falha > Clicar em **View Logs**.
3. Checar os logs do agente `vsbkp.log` ou `FileScan.log`:
   - *Cenário 1: "VSS Snapshot creation failed on Windows guest OS"* -> O serviço de Volume Shadow Copy do Windows está parado ou o disco não tem espaço livre suficiente (mínimo de 10% livre necessário para shadow storage).
   - *Cenário 2: "API rate limit exceeded during snapshot creation"* -> Muitas chamadas simultâneas de snapshot esgotaram o rate-limit da nuvem.

---

## 3. Ações de Remediação Imediata

### Cenário 1: Falha no VSS (Volume Shadow Copy) do Windows
Acessar o servidor via **AWS Systems Manager (Run Command)** e executar comando PowerShell:
```powershell
# 1. Checar status do serviço VSS
Get-Service -Name VSS

# 2. Reiniciar o serviço e limpar provedores órfãos
Restart-Service -Name VSS -Force
vssadmin list writers
```

### Cenário 2: Retentativa Manual com Janela Estendida
Se o erro foi timeout transitório de rede ou concorrência de I/O:
```bash
# Disparar manualmente o job de backup sob demanda para garantir a janela de RPO
aws backup start-backup-job \
  --backup-vault-name "EnterpriseDailyVault" \
  --resource-arn "arn:aws:rds:us-east-1:123456789012:db:prod-mysql-instance" \
  --iam-role-arn "arn:aws:iam::123456789012:role/service-role/AWSBackupDefaultServiceRole"
```

---

## 4. Registro no ITSM & Critérios de Escalação
* **Alerta no Freshservice:**
  - Registrar chamado vinculando o cliente e o ativo de infraestrutura afetado.
  - Anexar o log do erro retornado pelo Commvault ou AWS Backup.
* **Escalação:**
  - Caso o backup envolva o banco de dados principal de um cliente com SLA de RPO < 4 horas e a segunda tentativa falhar até as **05:30h**, acionar o **Administrador de Banco de Dados (DBA) ou Especialista de Armazenamento N3**.
