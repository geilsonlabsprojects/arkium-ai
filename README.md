# Arkium AI — Plataforma local de IA compatível com a API da OpenAI

API profissional que expõe os modelos do **Ollama** através de endpoints
**100% compatíveis com a OpenAI**, com painel administrativo em React.
Tudo local, tudo open source, sem serviços pagos.

---

## 1. Requisitos

| Software | Versão | Onde baixar |
|---|---|---|
| Python  | 3.12+ | https://www.python.org/downloads/ (marque **Add Python to PATH**) |
| Ollama  | atual | https://ollama.com/download |
| Node.js | 20+ (opcional, só para o painel) | https://nodejs.org |

Baixe pelo menos um modelo:

```bash
ollama pull llama3.2
# outros: qwen2.5, gemma2, deepseek-r1, mistral, phi3
```

## 2. Instalação (uma única vez)

**Windows:** dê duplo clique em `install.bat`
**Linux/macOS:** `chmod +x *.sh && ./install.sh`

O instalador verifica Python/pip/Ollama, cria o ambiente virtual, instala as
dependências, cria as pastas, o arquivo `.env`, o banco SQLite, as tabelas e o
administrador padrão.

## 3. Iniciar

**Windows:** `start.bat`  •  **Linux/macOS:** `./start.sh`

| Serviço | URL |
|---|---|
| Painel | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

Login padrão: **admin@arkium.ai** / **admin123** (troque no primeiro acesso).

Outros scripts: `stop.bat` / `stop.sh` (parar) e `update.bat` (atualizar).

## 4. Usando a API

Crie uma API Key no painel (**API Keys → Criar chave**) e use qualquer SDK da OpenAI:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="ark-SUA_CHAVE")
r = client.chat.completions.create(model="llama3.2",
        messages=[{"role": "user", "content": "Olá!"}])
print(r.choices[0].message.content)
```

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer ark-SUA_CHAVE" -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","messages":[{"role":"user","content":"Olá!"}],"stream":true}'
```

### Endpoints compatíveis

| Método | Rota | Descrição |
|---|---|---|
| GET | `/v1/models` | modelos instalados no Ollama |
| GET | `/v1/models/{id}` | detalhes de um modelo |
| POST | `/v1/chat/completions` | chat, com streaming SSE |
| POST | `/v1/completions` | texto puro, com streaming SSE |
| POST | `/v1/embeddings` | embeddings (requer `nomic-embed-text`) |

Streaming segue o padrão SSE da OpenAI, encerrando com `data: [DONE]`.

## 5. Configuração (`.env`)

| Variável | Função |
|---|---|
| `PORT` / `HOST` | porta e interface da API |
| `DATABASE_URL` | SQLite por padrão; troque por `postgresql+psycopg://...` para migrar |
| `SECRET_KEY` | chave de assinatura do JWT — **troque em produção** |
| `CORS_ORIGINS` | domínios liberados |
| `OLLAMA_HOSTS` | um ou vários servidores Ollama separados por vírgula |
| `DEFAULT_MODEL` / `DEFAULT_TEMPERATURE` / `DEFAULT_MAX_TOKENS` | padrões de inferência |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | limite por chave/usuário |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | administrador criado na instalação |

Modelo padrão, temperatura, tokens, timeout, rate limit, nome e logo também são
editáveis em **Configurações**, sem reiniciar.

### Mudar a porta
Altere `PORT` no `.env` e reinicie. Para o painel, ajuste o proxy em
`frontend/vite.config.ts`.

### Usar um domínio
Publique o backend atrás de Nginx/Caddy apontando para `127.0.0.1:8000`,
adicione o domínio em `CORS_ORIGINS` e sirva `frontend/dist` (gerado por
`npm run build`) como estático.

## 6. Estrutura

```
backend/app/  api/(routes, middlewares) core/ db/ models/ schemas/ services/
frontend/src/ pages/ components/ layouts/ hooks/ services/
scripts/      backup.py restore.py clean_logs.py clean_cache.py update_deps.py
```

## 7. Manutenção

```bash
python scripts/backup.py                       # backup do banco
python scripts/restore.py backups/arquivo.db   # restaurar
python scripts/clean_logs.py                   # limpar logs
python scripts/clean_cache.py                  # limpar caches
python scripts/update_deps.py                  # atualizar dependências
```

## 8. Recursos do painel

Dashboard com gráficos (Chart.js), monitoramento de CPU/RAM/disco e modelos
carregados, gestão de usuários, API Keys (criar, renomear, revogar, uso/IP),
playground de chat com streaming e cancelamento, histórico exportável, logs
com filtro de erros, configurações, documentação, tema claro/escuro e layout
responsivo.

## 9. Segurança

Senhas com bcrypt, JWT assinado, API keys armazenadas apenas como hash SHA-256,
rate limit por chave, headers defensivos (Helmet-equivalente), CORS restrito,
validação Pydantic em todas as entradas e mensagens de erro sem stack trace.

## 10. Migrar para Linux/VPS

Copie a pasta, rode `./install.sh`, ajuste o `.env` e sirva com
`uvicorn app.main:app --host 0.0.0.0 --port 8000` atrás de um proxy reverso.
Nenhuma alteração de código é necessária.
