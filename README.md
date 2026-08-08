# 🧠 Arkium AI

### Plataforma local de IA compatível com a API da OpenAI

O **Arkium AI** é uma plataforma profissional para executar e disponibilizar modelos de inteligência artificial localmente através do **Ollama**, oferecendo uma API **compatível com a OpenAI** e um painel administrativo moderno desenvolvido em React.

Tudo local.
Tudo open source.
Sem dependência de serviços pagos.

---

## ✨ Principais recursos

* 🤖 Integração com Ollama
* 🔌 API compatível com OpenAI
* 🔑 Gerenciamento de API Keys
* 👥 Gerenciamento de usuários
* 🚦 Rate limiting
* 📊 Dashboard com métricas
* 💻 Monitoramento de CPU, RAM e armazenamento
* 🧠 Gerenciamento de modelos
* 💬 Playground de chat
* ⚡ Streaming SSE
* 📜 Histórico de conversas
* 📝 Sistema de logs
* ⚙️ Configurações pelo painel
* 🌙 Tema claro e escuro
* 📱 Interface responsiva
* 📚 Swagger e ReDoc
* 💾 Backup e restauração do banco
* 🗄️ SQLite ou PostgreSQL
* 🔐 JWT + bcrypt + API Keys com hash SHA-256
* 🌐 Suporte a múltiplos servidores Ollama

---

# 🏗️ Arquitetura

O Arkium funciona como uma camada entre suas aplicações e os servidores Ollama.

```text
                    ┌─────────────────────┐
                    │      Aplicação      │
                    │   OpenAI SDK / API  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       ARKIUM        │
                    │      API / v1       │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
        API Keys          Rate Limit         Autenticação
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Ollama        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
           Llama            Qwen             Gemma
```

O Arkium também pode trabalhar com múltiplos servidores Ollama através da configuração `OLLAMA_HOSTS`.

---

# 📋 Requisitos

| Software   | Versão     | Obrigatório |
| ---------- | ---------- | ----------- |
| Python     | 3.12+      | ✅           |
| Ollama     | Atual      | ✅           |
| Node.js    | 20+        | Opcional    |
| PostgreSQL | Compatível | Opcional    |

### Downloads

* Python: https://www.python.org/downloads/
* Ollama: https://ollama.com/download
* Node.js: https://nodejs.org

> Ao instalar o Python no Windows, marque **Add Python to PATH**.

---

# 🦙 1. Instalar um modelo

Depois de instalar o Ollama, baixe pelo menos um modelo:

```bash
ollama pull llama3.2
```

Outros modelos compatíveis incluem:

```text
qwen2.5
gemma2
deepseek-r1
mistral
phi3
```

Você pode instalar quantos modelos desejar, desde que seu hardware possua recursos suficientes para executá-los.

---

# 🚀 2. Instalação

A instalação é feita uma única vez.

## Windows

Execute:

```text
install.bat
```

O instalador verifica automaticamente:

* Python;
* pip;
* Ollama;
* ambiente virtual;
* dependências;
* diretórios necessários;
* arquivo `.env`;
* banco SQLite;
* tabelas;
* administrador inicial.

## Linux / macOS

Execute:

```bash
chmod +x *.sh
./install.sh
```

---

# ▶️ 3. Iniciar o Arkium

## Windows

```text
start.bat
```

## Linux / macOS

```bash
./start.sh
```

Após iniciar, os serviços estarão disponíveis em:

| Serviço    | Endereço                    |
| ---------- | --------------------------- |
| 🎨 Painel  | http://localhost:5173       |
| 🔌 API     | http://localhost:8000       |
| 📚 Swagger | http://localhost:8000/docs  |
| 📖 ReDoc   | http://localhost:8000/redoc |

---

# 🔐 Primeiro acesso

O administrador inicial é criado durante a instalação.

```text
E-mail: admin@arkium.ai
Senha: admin123
```

> ⚠️ **Altere a senha imediatamente após o primeiro acesso.**

Em ambientes de produção, utilize uma senha forte e exclusiva.

---

# 🔌 4. Utilizando a API

O Arkium foi desenvolvido para ser compatível com a API da OpenAI.

Isso significa que aplicações que utilizam SDKs compatíveis podem apontar para o Arkium através do parâmetro `base_url`.

## Python + OpenAI SDK

Instale o SDK:

```bash
pip install openai
```

Depois:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="ark-SUA_CHAVE"
)

response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {
            "role": "user",
            "content": "Olá!"
        }
    ]
)

print(response.choices[0].message.content)
```

---

# 🌐 Exemplo com cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer ark-SUA_CHAVE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {
        "role": "user",
        "content": "Olá!"
      }
    ],
    "stream": true
  }'
```

---

# 📡 Endpoints compatíveis

| Método | Endpoint               | Descrição                |
| ------ | ---------------------- | ------------------------ |
| `GET`  | `/v1/models`           | Lista modelos instalados |
| `GET`  | `/v1/models/{id}`      | Detalhes de um modelo    |
| `POST` | `/v1/chat/completions` | Chat completions         |
| `POST` | `/v1/completions`      | Geração de texto         |
| `POST` | `/v1/embeddings`       | Geração de embeddings    |

### Streaming

O streaming utiliza **Server-Sent Events (SSE)** seguindo o padrão utilizado pela OpenAI.

A transmissão é encerrada com:

```text
data: [DONE]
```

---

# 🧩 Embeddings

Para utilizar:

```text
/v1/embeddings
```

é necessário possuir um modelo de embeddings compatível instalado no Ollama.

Por exemplo:

```bash
ollama pull nomic-embed-text
```

---

# ⚙️ 5. Configuração

As configurações principais ficam no arquivo:

```text
.env
```

Exemplo:

```env
PORT=8000
HOST=0.0.0.0

DATABASE_URL=sqlite:///./arkium.db

SECRET_KEY=CHANGE_THIS_SECRET_KEY

CORS_ORIGINS=http://localhost:5173

OLLAMA_HOSTS=http://localhost:11434

DEFAULT_MODEL=llama3.2
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2048

RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60

ADMIN_EMAIL=admin@arkium.ai
ADMIN_PASSWORD=CHANGE_THIS_PASSWORD
```

> Os valores acima são apenas exemplos. Utilize as configurações apropriadas para seu ambiente.

---

# 🗄️ Banco de dados

O Arkium utiliza SQLite por padrão.

Para ambientes maiores, é possível utilizar PostgreSQL.

### SQLite

```env
DATABASE_URL=sqlite:///./arkium.db
```

### PostgreSQL

```env
DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@HOST/BANCO
```

---

# 🦙 Múltiplos servidores Ollama

O Arkium permite configurar mais de um servidor Ollama.

Utilize:

```env
OLLAMA_HOSTS=http://localhost:11434,http://192.168.1.100:11434
```

Isso permite que o Arkium trabalhe com diferentes instâncias do Ollama.

---

# 🔑 API Keys

As API Keys podem ser gerenciadas diretamente pelo painel:

```text
API Keys → Criar chave
```

As chaves são utilizadas para autenticar aplicações que acessam a API.

Exemplo:

```http
Authorization: Bearer ark-SUA_CHAVE
```

As chaves não devem ser compartilhadas publicamente.

---

# 🚦 Rate Limiting

O Arkium possui controle de requisições por chave/usuário.

Configuração:

```env
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
```

No exemplo acima:

```text
60 requisições
      │
      ▼
a cada 60 segundos
```

---

# 🎛️ Configurações pelo painel

Diversas configurações podem ser alteradas diretamente através do painel administrativo, sem necessidade de editar o `.env` ou reiniciar o servidor.

Entre elas:

* modelo padrão;
* temperatura;
* quantidade máxima de tokens;
* timeout;
* rate limit;
* nome da aplicação;
* logo;
* configurações gerais.

---

# 🖥️ Painel administrativo

O painel do Arkium oferece uma interface centralizada para gerenciamento da plataforma.

### Dashboard

Exibe informações como:

* utilização de CPU;
* utilização de RAM;
* armazenamento;
* modelos carregados;
* métricas da plataforma.

### Usuários

Gerenciamento dos usuários do sistema.

### API Keys

Permite:

* criar;
* renomear;
* revogar;
* visualizar utilização;
* consultar IPs associados.

### Playground

Permite testar os modelos diretamente pelo painel através de um chat com:

* streaming;
* cancelamento;
* seleção de modelo.

### Histórico

Conversas podem ser consultadas e exportadas.

### Logs

Sistema de logs com filtros para facilitar a identificação de erros.

### Configurações

Gerenciamento das configurações da plataforma.

### Interface

O painel possui:

* tema claro;
* tema escuro;
* layout responsivo.

---

# 📚 Documentação da API

O Arkium disponibiliza documentação automática através do FastAPI.

## Swagger

```text
http://localhost:8000/docs
```

## ReDoc

```text
http://localhost:8000/redoc
```

Essas interfaces permitem visualizar e testar os endpoints disponíveis.

---

# 📁 6. Estrutura do projeto

```text
Arkium/
│
├── backend/
│   └── app/
│       ├── api/
│       │   ├── routes/
│       │   └── middlewares/
│       │
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       └── services/
│
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── layouts/
│       ├── hooks/
│       └── services/
│
├── scripts/
│   ├── backup.py
│   ├── restore.py
│   ├── clean_logs.py
│   ├── clean_cache.py
│   └── update_deps.py
│
├── install.bat
├── start.bat
├── stop.bat
├── update.bat
│
├── install.sh
├── start.sh
└── README.md
```

---

# 🛠️ 7. Manutenção

O Arkium possui scripts para manutenção do sistema.

## Backup

```bash
python scripts/backup.py
```

## Restaurar

```bash
python scripts/restore.py backups/arquivo.db
```

## Limpar logs

```bash
python scripts/clean_logs.py
```

## Limpar cache

```bash
python scripts/clean_cache.py
```

## Atualizar dependências

```bash
python scripts/update_deps.py
```

---

# 🌐 8. Usando um domínio

Para publicar o Arkium na Internet, recomenda-se utilizar um reverse proxy como:

* Nginx;
* Caddy.

O backend deve ficar protegido atrás do proxy reverso.

Exemplo:

```text
                    Internet
                       │
                       ▼
                  HTTPS / TLS
                       │
                       ▼
                 Nginx / Caddy
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Arkium API            Frontend
        :8000                  :5173
             │
             ▼
           Ollama
```

Adicione seu domínio em:

```env
CORS_ORIGINS=https://seu-dominio.com
```

Para produção, o frontend pode ser compilado com:

```bash
npm run build
```

E os arquivos gerados em:

```text
frontend/dist
```

podem ser servidos como conteúdo estático.

---

# 🐧 9. Migrando para Linux / VPS

Copie o projeto para o servidor.

Execute:

```bash
./install.sh
```

Configure o:

```text
.env
```

Depois, o backend pode ser executado com:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Para produção, recomenda-se executar o Arkium atrás de um proxy reverso.

Nenhuma alteração no código é necessária apenas para realizar a migração para Linux/VPS.

---

# 🔒 10. Segurança

O Arkium possui diversas camadas de proteção.

### Senhas

As senhas são protegidas utilizando:

```text
bcrypt
```

### Autenticação

O sistema utiliza:

```text
JWT
```

### API Keys

As API Keys são armazenadas utilizando:

```text
SHA-256
```

### Rate Limiting

As requisições são limitadas por chave/usuário.

### CORS

O acesso é controlado através de origens permitidas.

### Validação

As entradas da API são validadas utilizando:

```text
Pydantic
```

### Headers

O sistema utiliza headers defensivos para aumentar a segurança da aplicação.

### Erros

Mensagens de erro não devem expor stack traces internos para clientes.

---

# ⚠️ Segurança em produção

Antes de disponibilizar o Arkium publicamente:

* altere a senha do administrador;
* altere o `SECRET_KEY`;
* utilize HTTPS;
* configure corretamente o CORS;
* utilize um firewall;
* não exponha o Ollama diretamente à Internet;
* utilize senhas fortes;
* mantenha o sistema atualizado;
* faça backups periódicos.

**Nunca publique o arquivo `.env` no GitHub.**

Adicione-o ao `.gitignore`:

```gitignore
.env
*.db
backups/
```

---

# 🧪 Desenvolvimento

Clone o projeto:

```bash
git clone <URL_DO_REPOSITORIO>
cd Arkium
```

Instale as dependências do backend conforme o projeto e, para o frontend:

```bash
cd frontend
npm install
```

Execute o ambiente de desenvolvimento:

```bash
npm run dev
```

---

# 🤝 Contribuindo

Contribuições são bem-vindas.

### 1. Faça um Fork

Crie uma cópia do projeto na sua conta do GitHub.

### 2. Crie uma branch

```bash
git checkout -b feature/minha-feature
```

### 3. Faça suas alterações

Implemente e teste sua contribuição.

### 4. Faça o commit

```bash
git commit -m "feat: adiciona minha feature"
```

### 5. Envie a branch

```bash
git push origin feature/minha-feature
```

### 6. Abra um Pull Request

Explique claramente:

* o que foi alterado;
* por que a alteração foi necessária;
* como testar;
* possíveis impactos.

---

# 🗺️ Roadmap

O Arkium está em desenvolvimento contínuo.

Possíveis melhorias futuras incluem:

* [ ] Sistema avançado de permissões
* [ ] Mais métricas
* [ ] Monitoramento avançado
* [ ] Melhorias no sistema de logs
* [ ] Mais opções de gerenciamento de modelos
* [ ] Melhorias de escalabilidade
* [ ] Docker / Docker Compose
* [ ] Documentação expandida
* [ ] SDKs oficiais
* [ ] Melhorias na administração de múltiplos servidores Ollama

> O roadmap pode ser alterado conforme o desenvolvimento do projeto.

---

# 📜 Licença

O Arkium é distribuído sob uma licença de atribuição que permite:

* uso pessoal;
* uso comercial;
* modificação;
* distribuição;
* criação de versões derivadas.

### Atribuição obrigatória

Ao redistribuir o Arkium, ou uma versão modificada do projeto, os créditos do autor original devem permanecer presentes.

Não é permitido remover a atribuição original ou apresentar uma versão modificada como se fosse o projeto original.

Consulte o arquivo [`LICENSE`](LICENSE) para os termos completos.

---

# 👤 Autor

**Arkium AI**

Desenvolvido por **<Geilson_Labs_Projects>**.

GitHub:

**<https://github.com/geilsonlabsprojects>**

---

# ⭐ Apoie o projeto

Se o Arkium foi útil para você:

⭐ Dê uma estrela no GitHub.

🐛 Reporte problemas.

💡 Envie sugestões.

🔧 Contribua com o projeto.

📢 Compartilhe o Arkium.

---

# 📌 Status

**Em desenvolvimento**

O Arkium continua evoluindo e algumas funcionalidades, endpoints e configurações podem sofrer alterações entre versões.

Para ambientes de produção, recomenda-se acompanhar as versões e alterações do projeto.

---

## Copyright

Copyright © 2026 **<Geilson_Labs_Projects>**

**Arkium AI — Plataforma local de IA compatível com a API da OpenAI.**
