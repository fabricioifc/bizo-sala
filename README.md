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

O usuário inicial é criado com `ADMIN_EMAIL` / `ADMIN_SENHA` do `.env` quando o banco
está vazio. Para aplicar uma mudança desses valores a um usuário já existente:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d api
```

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec api python -m app.cli redefinir-usuario
```

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

Publicado em **https://sala.bizo.dev.br** via Cloudflare Tunnel. O HTTPS fica com a
Cloudflare; o nginx escuta só em `127.0.0.1:8080` no VPS.

1. Suba a aplicação:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

2. No túnel (Cloudflare Zero Trust → Networks → Tunnels → Public Hostname), crie
   `sala.bizo.dev.br` apontando para:
   - `http://localhost:8080`, se o `cloudflared` roda direto no VPS; ou
   - `http://nginx:80`, se usar o `cloudflared` deste compose
     (`TUNNEL_TOKEN` no `.env` e `--profile tunnel` no comando acima).
