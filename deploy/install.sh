#!/usr/bin/env bash
# Maestro — deploy script (Docker Swarm)
# Roda no VPS Case: cd /opt/maestro && bash deploy/install.sh

set -e

REPO_DIR="${REPO_DIR:-/opt/maestro}"
cd "$REPO_DIR"

echo "=== Maestro install @ $(date) ==="

# 1. Claude accounts
if [ ! -d /root/.claude-accounts ]; then
    echo "⚠️  /root/.claude-accounts não existe. Precisa setup inicial."
    echo "   Esse dir tem credentials.json de cada conta Max."
    exit 1
fi

# 2. .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  .env criado a partir de .env.example. Edita antes de continuar:"
    echo "   - CLICKUP_TOKEN"
    echo "   - EVOLUTION_KEY"
    exit 1
fi

# 3. Build local image
echo "→ Build maestro:latest"
docker build -t maestro:latest .

# 4. Deploy stack (Swarm) — volumes are auto-created with stack prefix: maestro_maestro_claude
echo "→ Stack deploy: maestro"
docker stack deploy -c docker-compose.yml maestro --resolve-image never

# 5. Seed Claude pool state (only if not already seeded)
sleep 3
CLAUDE_VOL=$(docker volume inspect maestro_maestro_claude --format '{{.Mountpoint}}' 2>/dev/null || echo "")
if [ -n "$CLAUDE_VOL" ] && [ ! -f "$CLAUDE_VOL/maestro_accounts_state.json" ]; then
    echo "→ Seeding Claude pool state"
    cat > "$CLAUDE_VOL/maestro_accounts_state.json" <<EOF
{
  "active": "account2",
  "accounts": {
    "account2": {"email": "infra@queilatrizotti.com.br", "cooldown_until": 0},
    "account3": {"email": "adm@queilacomque.com.br", "cooldown_until": 0}
  }
}
EOF
    cp /root/.claude-accounts/account2/credentials.json "$CLAUDE_VOL/.credentials.json"
    chmod 600 "$CLAUDE_VOL/.credentials.json" "$CLAUDE_VOL/maestro_accounts_state.json"
    docker service update --force maestro_maestro >/dev/null
fi

echo ""
echo "✓ Maestro deployed"
echo ""
sleep 3
docker service ls --filter name=maestro
echo ""
echo "Logs: docker service logs -f maestro_maestro"
echo "Webhook URL: https://maestro.manager01.casein.com.br/webhook/maestro"
echo "Health:      https://maestro.manager01.casein.com.br/health"
