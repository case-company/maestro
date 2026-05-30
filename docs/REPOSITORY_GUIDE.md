# Repository Guide — maestro

Este guia padroniza a operação deste repositório para passagem de bastão, manutenção segura e evolução sem quebrar interface ou produção.

## Identidade

- **Tipo:** `ops-bot`
- **Branch analisada:** `main`
- **Arquivos versionados detectados:** 25
- **Deploy/infra detectado:** Dockerfile detectado.

## Setup Local

Instalação sugerida:

```bash
pip install -r requirements.txt
```

Comandos conhecidos:

- `docker compose up -d` -> subir assistente operacional

## Estrutura de Configuração

Configs detectados:

`Dockerfile`, `docker-compose.yml`

Variáveis esperadas por exemplo/local:

`EVOLUTION_URL`, `EVOLUTION_KEY`, `EVOLUTION_INSTANCE`, `MAESTRO_WA_JID`, `CLICKUP_TOKEN`, `CLICKUP_TEAM_CASE`, `MAESTRO_PORT`, `MAESTRO_LOG_LEVEL`, `MAESTRO_ALLOWED_JIDS`, `WHISPER_MODEL`, `WHISPER_COMPUTE_TYPE`

> Nunca coloque valores reais de segredos neste arquivo, no README, em screenshots ou em exemplos versionados. Documente apenas o nome da variável e guarde o valor no cofre oficial.

## Rotas e Pontos de Atenção

Arquivos de rota/API detectados no scan:

- Nenhuma rota/API detectada automaticamente.

## Regra de Ouro para Frontend

Para não quebrar front-end durante organização ou handoff:

- Não altere `src/`, `app/`, `pages/`, `components/`, `public/`, CSS, assets, `package.json`, lockfiles ou configs de build em PRs de organização.
- PRs de organização devem tocar apenas documentação, templates GitHub, ignores, metadados e guias.
- Qualquer mudança visual precisa de screenshot antes/depois, teste mobile/desktop e validação do fluxo principal.
- Se o repo usa Vercel/Lovable/Vite/Next, confirme que o build local continua passando antes de pedir review.

## Checklist de Pull Request

- [ ] Mudança classificada como docs/meta, frontend, backend, dados ou infra.
- [ ] Nenhum segredo real foi adicionado.
- [ ] Arquivos de runtime foram evitados quando a intenção era só organização.
- [ ] Build/test/lint aplicável foi rodado ou a impossibilidade foi documentada.
- [ ] Deploy e rollback foram considerados para mudanças de produção.
- [ ] Handoff atualizado quando a mudança altera operação, envs, deploy ou dados.

## Handoff

Antes de entregar este repo a outra pessoa, confirme:

- [ ] README indica o que o sistema faz e quem usa.
- [ ] `docs/REPOSITORY_GUIDE.md` está atual.
- [ ] Variáveis estão no cofre, não em docs.
- [ ] Deploy canônico está documentado.
- [ ] Owner de produto e owner técnico estão definidos.
- [ ] Riscos conhecidos estão em issue aberta ou documento de backlog.
