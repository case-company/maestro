# Contributing

Obrigado por contribuir com este repositório. Este projeto faz parte do ecossistema Case/ALL IN e deve ser mantido com foco em segurança, previsibilidade e passagem de bastão clara.

## Fluxo

1. Abra uma branch curta e descritiva.
2. Faça mudanças pequenas e revisáveis.
3. Não misture organização de repo com mudança de produto.
4. Atualize documentação quando alterar comportamento, deploy, envs ou dados.
5. Abra PR usando o template do repositório.

## Setup

```bash
pip install -r requirements.txt
```

Comandos conhecidos:

- `docker compose up -d` -> subir assistente operacional

## Frontend

Mudanças em frontend exigem cuidado extra: screenshot antes/depois, validação mobile/desktop e teste do fluxo principal. PRs de documentação ou organização não devem tocar código de interface.

## Segurança

Nunca commite valores reais de `.env`, tokens, chaves Supabase service role, OAuth secrets, cookies, export de banco ou credenciais de produção. Use placeholders e guarde valores no cofre oficial.
