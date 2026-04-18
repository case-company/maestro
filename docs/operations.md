# Maestro — Operações

## Deploy inicial no VPS Case

### Pré-requisitos no VPS
- Docker + Docker Compose instalados
- Rede Traefik external (`docker network ls | grep traefik`). Se não existe, cria: `docker network create traefik`
- DNS do domínio `maestro.manager01.casein.com.br` → IP do VPS (Cloudflare/provedor)
- Contas Claude Max em `/root/.claude-accounts/<slug>/` (credentials.json por conta)

### Passos

```bash
# 1. Clone/copia repo pro VPS
cd /opt
git clone <repo_url> maestro
# ou: scp -r ~/code/maestro-case root@<ip>:/opt/maestro
cd /opt/maestro

# 2. Configura .env
cp .env.example .env
nano .env  # preencher CLICKUP_TOKEN

# 3. Build + start
bash deploy/install.sh

# 4. Aponta webhook Evolution
bash deploy/setup-webhook.sh
```

### Teste

```bash
# Health check
curl https://maestro.manager01.casein.com.br/health

# Envia msg WhatsApp pro número Maestro (+55 11 91352-9334) via DM
# Deve responder o welcome
```

## Operação dia a dia

### Ver logs
```bash
docker compose logs -f maestro --tail=100
```

### Restart após mudança de código
```bash
docker compose up -d --build
```

### Ver state de um user
```bash
docker exec maestro cat /data/state/5527999087857_s.whatsapp.net.json
```

### Journal (audit trail)
```bash
docker exec maestro tail -100 /data/journal.jsonl | jq .
```

### Rotação Claude accounts

Ver status:
```bash
docker exec maestro python3 -c "import sys; sys.path.insert(0,'/app'); import accounts; print(accounts.status())"
```

Forçar switch:
```bash
docker exec maestro python3 -c "import sys; sys.path.insert(0,'/app'); import accounts; print(accounts.switch_to('account2'))"
```

## Adicionar nova conta Max

1. Rodar OAuth flow no host (ver script `oauth_direct.py`)
2. Copiar `credentials.json` pro volume: `docker cp credentials.json maestro:/root/.claude-accounts/account5/`
3. Registrar: `/accounts add account5` via WA

## Troubleshooting

### Webhook não recebe
- `curl -H "apikey: $EVOLUTION_KEY" $EVOLUTION_URL/webhook/find/maestro`
- Verifica DNS: `dig maestro.manager01.casein.com.br`
- Traefik logs: `docker logs traefik | grep maestro`

### Maestro não responde user
- `docker logs maestro --tail=50 | grep MSG`
- Verifica allowlist: `grep ALLOWED /opt/maestro/.env`
- JID do user bate? WhatsApp usa formato `NUMERO@s.whatsapp.net`

### Todas contas Claude em cooldown
- `/pool` via WA mostra status
- `/pool reset` zera (cuidado — vai bater cap real e ficar ainda mais tempo)
- Adicionar +1 conta (best option)

### Transcrição travou
- faster-whisper ocupa ~2GB RAM quando warm. VPS precisa de ≥ 4GB pra confortável
- `docker stats maestro` pra ver uso
- Se OOM, reduz `WHISPER_MODEL` pra `small` no .env
