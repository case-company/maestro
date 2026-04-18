# Maestro — Case/All In

Assistente operacional WhatsApp pro time Case/All In. Só aceita DMs do time autorizado. Processa conteúdo encaminhado (áudios, texto, imagens) e transforma em tasks ClickUp ou anexos contextuais.

## Arquitetura

```
WhatsApp (DM privado do time)
   ↓ (forward)
Evolution API (instance "maestro")
   ↓ webhook
Maestro Webhook (Flask)
   ↓
Router (input guardian Pedro Valério)
   ↓
┌──────┬──────────┬────────────┐
Task   Anexo em   Memória      Clone
creator task      contextual   (voice DNA)
  ↓      ↓         ↓             ↓
  ClickUp All In (Case / Sprint / Mentorada)
```

## Stack

- **Flask** (Python) webhook
- **faster-whisper** transcrição
- **Claude Max** via OAuth (contas ALL IN rotacionadas)
- **ClickUp API v2** (team `9011530618`)
- **Evolution API** (instance `maestro` no VPS Case)
- **Docker Compose** deploy

## Allowlist

Hoje o time autorizado a usar Maestro:
- Kaique (5511964682447)
- Queila (5567991076464)
- Mariza (5562998614114)
- Gobbi (5527999087857)
- Hugo (5527999739466)
- Heitor (5527999473185)
- Lara (5524992514909)

Qualquer outro número → silence.

## Comandos principais

- `/x` — transcreve áudio encaminhado
- `/task <descrição>` — cria task (pergunta prefixo se não claro)
- `/task case:<mentorada> <desc>` — cria task mentorada específica
- `/task allin:<desc>` — task sprint atual All In
- `/anexo #<task_id>` — anexa último conteúdo em task existente
- `/sot <mentorada>` — resumo do contexto daquela mentorada
- `/help` — comandos completos

## Deploy

```bash
git clone <repo> maestro
cd maestro
cp .env.example .env
# editar .env: cole creds ClickUp, Evolution key, etc
docker compose up -d
```

Webhook Evolution vai ser apontado pra `https://maestro.manager01.casein.com.br/webhook/maestro`

## Framework embutido

1. **PAI Miessler**: TELOS Case, substrate operacional, clones voice DNA
2. **Pedro Valério**: 4 executores, 3 níveis, quality gates blocking, entidades, herança top-down
3. **Gobbi ClickUp schema**: custom fields canônicos, naming convention, automations
