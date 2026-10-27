# Bizo Sala

Gestão de turmas do IFC Videira: chamada, conteúdo, carga horária, notas,
recuperação e mensagens por e-mail. Regras e convenções em [AGENTS.md](AGENTS.md).

## Desenvolvimento

```bash
cp .env.example .env   # preencha os valores
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

| Serviço | Endereço |
|---|---|
| Aplicação (Vue) | http://localhost:5173 |
| API / documentação | http://localhost:8000/api/docs |
| Mailpit (e-mails de dev) | http://localhost:8025 |

O usuário inicial é criado com `ADMIN_EMAIL` / `ADMIN_SENHA` do `.env`.

### Verificações

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api sh -c "ruff check . && ruff format --check . && mypy app && pytest"
```

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web sh -c "npm run lint && npm run type-check && npm run test"
```

Depois de mudar a API, regenere os tipos do front:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web npm run gen:api
```

## Produção (VPS)

1. Aponte o domínio (`DOMAIN` no `.env`) para o IP do VPS.
2. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`

O Caddy emite o certificado HTTPS automaticamente.
