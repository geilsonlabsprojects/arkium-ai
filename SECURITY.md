# Security Policy

## Arkium AI

A segurança do Arkium é importante.

Se você encontrar uma vulnerabilidade de segurança, pedimos que não publique
as informações diretamente em uma Issue pública do GitHub.

Um relatório responsável permite que o problema seja analisado e corrigido
antes que informações que possam ser utilizadas para exploração sejam
divulgadas publicamente.

---

# 🔒 Versões suportadas

Como o Arkium está em desenvolvimento, a versão mais recente é a versão
prioritária para correções de segurança.

| Versão                     | Suporte                       |
| -------------------------- | ----------------------------- |
| Última versão estável      | ✅                             |
| Versões antigas            | ⚠️ Limitado                   |
| Versões de desenvolvimento | ⚠️ Pode não receber correções |

Recomenda-se sempre utilizar a versão mais recente disponível.

---

# 🚨 Reportando uma vulnerabilidade

**Não abra uma Issue pública para vulnerabilidades de segurança.**

Envie o relatório de forma privada através do canal de segurança configurado
pelos mantenedores do projeto.

### Contato

E-mail de segurança:

**<EM_BREVE>**

---

# 📝 O que incluir no relatório

Sempre que possível, inclua:

* descrição da vulnerabilidade;
* versão afetada;
* componente afetado;
* passos para reproduzir;
* impacto potencial;
* exemplo de exploração, quando necessário;
* evidências;
* sugestão de correção, se disponível.

Um relatório pode seguir este formato:

```text
Título:
[Descrição curta da vulnerabilidade]

Versão afetada:
1.0.0

Componente:
API / Autenticação

Descrição:
[Explique o problema]

Passos para reproduzir:
1. ...
2. ...
3. ...

Impacto:
[Explique o que um atacante poderia fazer]

Evidência:
[Logs, screenshots ou código mínimo, se necessário]

Sugestão:
[Possível correção]
```

---

# 🔐 Não envie informações sensíveis

Nunca inclua no relatório:

* senhas reais;
* API Keys reais;
* tokens de autenticação;
* chaves privadas;
* arquivos `.env`;
* dados pessoais;
* informações de usuários reais;
* credenciais de servidores.

Se uma prova de conceito precisar de credenciais, utilize credenciais
temporárias e fictícias.

---

# 🛡️ Áreas especialmente importantes

Ao avaliar o Arkium, algumas áreas merecem atenção especial:

### API Authentication

* API Keys;
* JWT;
* autenticação de usuários;
* expiração de tokens.

### Autorização

* permissões;
* acesso administrativo;
* isolamento entre usuários;
* endpoints protegidos.

### API

* validação de entrada;
* manipulação de requisições;
* rate limiting;
* CORS;
* exposição de informações.

### Banco de dados

* SQL injection;
* exposição de dados;
* permissões;
* armazenamento de credenciais.

### Painel administrativo

* autenticação;
* autorização;
* XSS;
* CSRF;
* gerenciamento de usuários.

### Integração com Ollama

* SSRF;
* URLs maliciosas;
* acesso indevido a servidores internos;
* exposição de serviços.

---

# ⏱️ Processo de resposta

Após receber um relatório válido, os mantenedores procurarão:

1. confirmar o recebimento;
2. reproduzir o problema;
3. avaliar a gravidade;
4. desenvolver uma correção;
5. testar a correção;
6. publicar uma atualização quando apropriado.

O prazo pode variar dependendo da complexidade e gravidade da vulnerabilidade.

---

# 📢 Divulgação

Vulnerabilidades confirmadas poderão ser divulgadas após uma correção estar
disponível.

A divulgação poderá incluir:

* descrição do problema;
* versões afetadas;
* versão corrigida;
* impacto;
* créditos ao pesquisador que realizou o relatório, quando autorizado.

---

# 🙏 Agradecimentos

Agradecemos pesquisadores e usuários que ajudam a melhorar a segurança do
Arkium através de relatórios responsáveis.

Pesquisadores que enviarem vulnerabilidades válidas poderão ser reconhecidos
nos créditos de segurança do projeto, caso desejem.
