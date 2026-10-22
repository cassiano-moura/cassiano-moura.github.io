# Modelo Formal de Gestão de Mudança (GMUD - ITIL Framework)

**Documento:** `GMUD-TEMPLATE-ITIL-V4`  
**Objetivo:** Padronização de requisições de mudança para o time de Operações de Atendimento e Sustentação Cloud.  
**Autor:** Cassiano Moura (Cloud Support Associate / NOC Operations)

---

## 1. Informações Gerais da Mudança

| Campo | Descrição / Valor |
| :--- | :--- |
| **Código da GMUD:** | `GMUD-2026-10-22-042` |
| **Título:** | Expansão de Volume EBS de 100GB para 250GB no Servidor de Produção `srv-app-prod-01` |
| **Tipo de Mudança:** | [X] **Padrão (Standard)** &nbsp;&nbsp; [ ] **Normal** &nbsp;&nbsp; [ ] **Emergencial** |
| **Impacto no Negócio:** | **Baixo** (Operação online com Elastic Block Store sem reboot do sistema operacional) |
| **Risco Técnico:** | **Baixo** (Procedimento testado em homologação com suporte a snapshot prévio) |
| **Solicitante:** | Time de FinOps & Capacidade / Alerta de Sustentação |
| **Executor Responsável:** | **Cassiano Moura** (Analista de Operações Cloud - Turno Noturno) |
| **Ambiente:** | Produção (AWS US-East-1 / Cliente Corporativo Dedalus) |
| **Janela de Execução:** | **23 de Outubro de 2026 — das 02:00h às 03:00h UTC-3 (Madrugada)** |

---

## 2. Justificativa Técnica & do Negócio
O volume de dados da aplicação (`/data`) atingiu **91% de ocupação**, disparando o alerta no Zabbix e violando o limiar de segurança operacional. A expansão para 250GB garante margem operacional de 6 meses de crescimento orgânico sem interrupção dos serviços.

---

## 3. Plano de Teste Prévio (Homologação)
O procedimento foi simulado no ambiente de Staging (`srv-app-stage-01`), comprovando que o comando `growpart` e `resize2fs` expandem a partição em menos de 15 segundos sem perda de pacotes ou desconexão de usuários.

---

## 4. Plano de Ação Passo a Passo (Checklist de Execução)

1. [ ] **02:00h — Comunicação de Início:** Atualizar o chamado no Freshservice informando início da janela de GMUD.
2. [ ] **02:05h — Criação de Snapshot de Segurança (Backup Pré-Mudança):**
   ```bash
   aws ec2 create-snapshot \
     --volume-id vol-0123456789abcdef0 \
     --description "Snapshot Pré-GMUD-2026-10-22-042 Expansao EBS" \
     --tag-specifications 'ResourceType=snapshot,Tags=[{Key=GMUD,Value=042},{Key=Owner,Value=CassianoMoura}]'
   ```
3. [ ] **02:15h — Modificação do Volume na AWS (Online):**
   ```bash
   aws ec2 modify-volume --volume-id vol-0123456789abcdef0 --size 250 --volume-type gp3
   ```
4. [ ] **02:20h — Conexão via AWS SSM e Extensão no Sistema Operacional:**
   ```bash
   # Expandir a partição física
   sudo growpart /dev/nvme0n1 1
   
   # Redimensionar o sistema de arquivos EXT4
   sudo resize2fs /dev/nvme0n1p1
   ```
5. [ ] **02:25h — Validação Pós-Mudança:**
   ```bash
   df -h /data
   # Esperado: Tamanho total 246G, Disponível > 150G, Uso < 40%
   ```
6. [ ] **02:30h — Comunicação de Sucesso:** Anexar evidência do `df -h` e encerrar a GMUD no ITSM.

---

## 5. Plano de Rollback Obrigatório (Procedimento de Reversão)

> **Critério de Acionamento do Rollback:** Caso ocorra travamento de I/O no disco por mais de 5 minutos, erro de montagem do filesystem ou corrupção de blocos após o comando de resize.

1. **Tempo Limite para Decisão de Rollback:** **02:40h** (garantindo 20 minutos de margem antes do fim da janela).
2. **Passo a Passo de Rollback:**
   - Desconectar a instância do tráfego através do Target Group do ALB.
   - Criar um novo volume EBS a partir do snapshot pré-GMUD criado no Passo 2:
     ```bash
     aws ec2 create-volume --snapshot-id <SNAPSHOT_ID> --availability-zone us-east-1a
     ```
   - Desanexar o volume corrompido e anexar o novo volume restaurado como `/dev/xvda`.
   - Iniciar o serviço e validar a integridade dos dados via script de health check.
   - Notificar o coordenador de operações e manter o chamado aberto em status de investigação.

---

## 6. Parecer Final e Aceite Operacional
* **Status da Execução:** [X] SUCESSO &nbsp;&nbsp; [ ] ROLLBACK EXECUTADO &nbsp;&nbsp; [ ] CANCELADA
* **Evidências Registradas:** Anexadas no ticket Freshservice `#TK-84921`.
