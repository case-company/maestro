#!/usr/bin/env bash
# Maestro — deploy script
# Roda no VPS Case: cd /opt/maestro && bash deploy/install.sh

set -e

REPO_DIR="${REPO_DIR:-/opt/maestro}"
cd "$REPO_DIR"

echo "=== Maestro install @ $(date) ==="

# 1. Copiar Claude creds das contas All In (já existentes no /root/.claude-accounts)
if [ ! -d /root/.claude-accounts ]; then
    echo "⚠️  /root/.claude-accounts não existe. Precisa setup inicial."
    echo "   Esse dir tem credentials.json de cada conta Max."
    exit 1
fi

# 2. .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  .env criado a partir de .env.example. Edita antes de continuar:"
    echo "   - CLICKUP_TOKEN (o token ALL IN do Gobbi)"
    echo "   - EVOLUTION_KEY (já preenchido)"
    exit 1
fi

# 3. Pre-mount: copia accounts pro volume
docker volume create maestro_claude 2>/dev/null || true

# 4. Build + up
docker compose build
docker compose up -d

echo "✓ Maestro rodando"
echo ""
echo "Webhook URL: https://maestro.manager01.casein.com.br/webhook/maestro"
echo "Health:      https://maestro.manager01.casein.com.br/health"
echo ""
echo "Próximo passo: configurar webhook da Evolution pra apontar pra cá:"
echo "  curl -X POST \$EVOLUTION_URL/webhook/set/maestro \\"
echo "    -H 'apikey: \$EVOLUTION_KEY' -H 'Content-Type: application/json' \\"
echo "    -d '{\"webhook\": {\"url\": \"https://maestro.manager01.casein.com.br/webhook/maestro\", \"events\": [\"MESSAGES_UPSERT\"]}}'"
