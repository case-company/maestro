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

# 4. Pre-mount volume Claude + seed accounts
docker volume create maestro_claude 2>/dev/null || true
CLAUDE_VOL_PATH=$(docker volume inspect maestro_claude --format '{{.Mountpoint}}')
mkdir -p "$CLAUDE_VOL_PATH/.claude-accounts"
cp -rn /root/.claude-accounts/* "$CLAUDE_VOL_PATH/.claude-accounts/" 2>/dev/null || true

# 5. Deploy stack (Swarm)
echo "→ Stack deploy: maestro"
docker stack deploy -c docker-compose.yml maestro --resolve-image never

echo ""
echo "✓ Maestro deployed"
echo ""
sleep 3
docker service ls --filter name=maestro
echo ""
echo "Logs: docker service logs -f maestro_maestro"
echo "Webhook URL: https://maestro.manager01.casein.com.br/webhook/maestro"
echo "Health:      https://maestro.manager01.casein.com.br/health"
