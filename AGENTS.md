# AGENTS.md

Orientações para agentes de IA e automações neste repositório.

## Prioridades

1. Preserve comportamento de produção.
2. Não toque em frontend/runtime quando a tarefa for apenas organização de repositório.
3. Antes de alterar UI, leia padrões existentes e valide visualmente em desktop e mobile.
4. Não adicione nem exponha segredos.
5. Prefira mudanças pequenas, com documentação do motivo.

## Áreas Sensíveis

- Variáveis de ambiente e secrets.
- Configs de deploy Vercel/Railway/Docker.
- Migrations Supabase/Postgres.
- Rotas de API e webhooks.
- Arquivos de UI, CSS, assets e lockfiles.

## Para Organização/Handoff

Mudanças de padronização devem se limitar a `.github/`, docs, `.editorconfig`, `.gitattributes`, `.gitignore`, `CONTRIBUTING.md`, `SECURITY.md` e guias operacionais.
