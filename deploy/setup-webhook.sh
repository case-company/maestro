#!/usr/bin/env bash
# Configura webhook da Evolution API pra apontar pro Maestro
set -e

source ../.env

WEBHOOK_URL="https://maestro.manager01.casein.com.br/webhook/maestro"

echo "=== Set webhook Evolution → Maestro ==="
curl -s -X POST \
  "${EVOLUTION_URL}/webhook/set/${EVOLUTION_INSTANCE}" \
  -H "apikey: ${EVOLUTION_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"webhook\": {
      \"enabled\": true,
      \"url\": \"${WEBHOOK_URL}\",
      \"events\": [\"MESSAGES_UPSERT\"],
      \"webhook_by_events\": false,
      \"webhook_base64\": false
    }
  }" | python3 -m json.tool

echo ""
echo "=== Verify webhook ==="
curl -s -H "apikey: ${EVOLUTION_KEY}" \
  "${EVOLUTION_URL}/webhook/find/${EVOLUTION_INSTANCE}" | python3 -m json.tool
