/** Documentacao da API no estilo OpenAI/Anthropic, com exemplos prontos. */

const PY = `from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="ark-SUA_CHAVE",
)

resposta = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Explique IA local em 1 frase."}],
)
print(resposta.choices[0].message.content)`;

const JS = `import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:8000/v1",
  apiKey: "ark-SUA_CHAVE",
});

const stream = await client.chat.completions.create({
  model: "llama3.2",
  messages: [{ role: "user", content: "Ola!" }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}`;

const CURL = `curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ark-SUA_CHAVE" \\
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Ola!"}],
    "stream": false
  }'`;

function Block({ title, code }: { title: string; code: string }) {
  return (
    <div className="card">
      <h3 className="mb-3 font-semibold">{title}</h3>
      <pre className="overflow-x-auto rounded-xl bg-muted p-4 text-xs leading-relaxed"><code>{code}</code></pre>
    </div>
  );
}

export default function Docs() {
  const endpoints = [
    ["GET", "/v1/models", "Lista os modelos instalados no Ollama"],
    ["GET", "/v1/models/{id}", "Detalhes de um modelo"],
    ["POST", "/v1/chat/completions", "Chat completions (com ou sem streaming)"],
    ["POST", "/v1/completions", "Completions de texto puro"],
    ["POST", "/v1/embeddings", "Embeddings (requer modelo de embedding)"],
  ];

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-2xl font-semibold">Documentacao da API</h1>
        <p className="mt-2 text-muted-foreground">
          Todos os endpoints seguem o contrato da OpenAI. Autentique com uma API key
          criada no painel, enviada no cabecalho <code className="rounded bg-muted px-1">Authorization: Bearer ark-...</code>.
        </p>
        <p className="mt-2 text-sm">
          Referencia interativa completa: <a className="text-primary" href="/docs" target="_blank" rel="noreferrer">Swagger UI</a>
        </p>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="border-b border-border text-left text-muted-foreground">
            <tr><th className="p-3">Metodo</th><th className="p-3">Endpoint</th><th className="p-3">Descricao</th></tr>
          </thead>
          <tbody>
            {endpoints.map(([m, path, desc]) => (
              <tr key={path} className="border-b border-border/60 last:border-0">
                <td className="p-3"><span className="badge bg-primary/10 text-primary">{m}</span></td>
                <td className="p-3 font-mono text-xs">{path}</td>
                <td className="p-3 text-muted-foreground">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Block title="Python (SDK oficial da OpenAI)" code={PY} />
        <Block title="JavaScript / TypeScript (streaming)" code={JS} />
      </div>
      <Block title="cURL" code={CURL} />
    </div>
  );
}
