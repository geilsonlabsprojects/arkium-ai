# Contributing to Arkium AI

Obrigado por querer contribuir com o **Arkium AI**.

O Arkium é um projeto open source e contribuições são bem-vindas, seja através
de código, correções de bugs, documentação, testes, sugestões ou melhorias
de segurança.

---

## 📋 Antes de começar

Antes de criar uma contribuição:

1. Verifique se já existe uma Issue relacionada.
2. Procure Pull Requests existentes para o mesmo problema.
3. Leia o README principal.
4. Certifique-se de que sua alteração está de acordo com os objetivos do projeto.

Para mudanças grandes, recomenda-se abrir uma Issue primeiro para discutir a
proposta antes de implementar.

---

# 🐛 Reportando bugs

Ao encontrar um problema, abra uma Issue contendo o máximo possível de
informações.

Inclua:

* versão do Arkium;
* sistema operacional;
* versão do Python;
* versão do Node.js;
* versão do Ollama;
* modelo utilizado;
* descrição do problema;
* passos para reproduzir;
* comportamento esperado;
* comportamento observado;
* mensagens de erro relevantes;
* logs relevantes.

### Exemplo

```text
Arkium: 1.0.0
Sistema: Windows 11
Python: 3.12.x
Node.js: 20.x
Ollama: atual
Modelo: llama3.2
```

Nunca publique:

* API Keys;
* senhas;
* tokens;
* arquivos `.env`;
* dados pessoais;
* credenciais;
* informações privadas do servidor.

---

# 💡 Sugestões

Sugestões de novas funcionalidades são bem-vindas.

Ao sugerir uma funcionalidade, explique:

1. Qual problema ela resolve;
2. Como você imagina que deveria funcionar;
3. Qual benefício ela traria;
4. Se existem alternativas atualmente.

---

# 🔧 Desenvolvimento

## 1. Faça um Fork

Faça um fork do repositório do Arkium para sua conta do GitHub.

## 2. Clone o projeto

```bash
git clone <URL_DO_SEU_FORK>
cd Arkium
```

## 3. Crie uma branch

Utilize nomes descritivos:

```bash
git checkout -b feature/nova-funcionalidade
```

ou:

```bash
git checkout -b fix/corrige-autenticacao
```

ou:

```bash
git checkout -b docs/melhora-documentacao
```

---

# 🐍 Backend

Instale as dependências necessárias de acordo com o projeto.

Utilize um ambiente virtual:

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

# ⚛️ Frontend

Entre no diretório:

```bash
cd frontend
```

Instale as dependências:

```bash
npm install
```

Execute o ambiente de desenvolvimento:

```bash
npm run dev
```

---

# 🧪 Testes

Antes de enviar um Pull Request:

* execute o backend;
* execute o frontend;
* teste as alterações;
* verifique a API;
* verifique o painel;
* confirme que funcionalidades existentes continuam funcionando.

Quando houver testes automatizados disponíveis, execute-os antes de enviar
a contribuição.

---

# 🧹 Qualidade do código

Procure manter o código:

* simples;
* legível;
* organizado;
* modular;
* documentado quando necessário;
* consistente com o código existente.

Evite alterações não relacionadas ao objetivo do Pull Request.

---

# 📝 Commits

Recomenda-se utilizar mensagens de commit claras.

Exemplos:

```text
feat: adiciona gerenciamento de modelos
```

```text
fix: corrige autenticação da API
```

```text
docs: atualiza documentação de instalação
```

```text
refactor: reorganiza serviço de modelos
```

```text
security: corrige validação de API key
```

---

# 🔀 Pull Requests

Antes de abrir um Pull Request:

* verifique se o código funciona;
* revise suas alterações;
* remova arquivos temporários;
* não inclua `.env`;
* não inclua banco de dados local;
* não inclua API Keys;
* atualize a documentação quando necessário.

O Pull Request deve explicar:

### O que foi alterado?

Descreva objetivamente as mudanças.

### Por que foi alterado?

Explique o problema ou necessidade.

### Como testar?

Informe os passos necessários para verificar a alteração.

---

# 🔐 Segurança

Problemas de segurança **não devem ser publicados em Issues públicas**.

Consulte o arquivo:

```text
SECURITY.md
```

para saber como realizar um relatório de segurança.

---

# 📚 Documentação

Melhorias na documentação também são contribuições importantes.

Você pode contribuir com:

* README;
* exemplos;
* tutoriais;
* documentação da API;
* comentários no código;
* correções ortográficas;
* traduções.

---

# 📜 Licença e atribuição

Ao contribuir com o Arkium, você concorda que sua contribuição poderá ser
distribuída sob a licença do projeto.

A licença do Arkium permite uso, modificação e distribuição, mas exige a
preservação da atribuição ao autor original.

Consulte o arquivo:

```text
LICENSE
```

para conhecer os termos completos.

---

# 🤝 Código de conduta

Esperamos que todos os colaboradores mantenham uma postura respeitosa,
profissional e construtiva.

Não serão tolerados:

* assédio;
* discriminação;
* ameaças;
* ataques pessoais;
* spam;
* comportamento deliberadamente abusivo.

O objetivo é manter um ambiente onde qualquer pessoa possa contribuir de
forma segura e produtiva.

---

# ⭐ Obrigado!

Toda contribuição ajuda o Arkium a evoluir.

Obrigado por contribuir com o projeto!
