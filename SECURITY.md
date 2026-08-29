# Security Policy

## Reporting

Não abra issue pública com segredo, token, dump de banco, telefone, email de cliente/mentorado ou detalhe explorável. Reporte diretamente ao owner técnico do projeto e registre a correção em canal privado.

## Secrets

- Valores reais ficam fora do Git.
- Arquivos `.env`, `.env.local`, `.env.production` e equivalentes devem estar ignorados.
- `.env.example` deve conter somente nomes e placeholders.
- Se um segredo for versionado, rotacione imediatamente antes de apenas remover do arquivo.

## Pull Requests

Toda PR deve confirmar que não adiciona segredo real e que dados sensíveis foram anonimizados.
