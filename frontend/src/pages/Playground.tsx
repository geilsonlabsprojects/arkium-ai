import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, getToken } from "../services/api";
import type { ModelsResponse } from "../services/types";
import { useToast } from "../components/Toast";

interface Msg { role: "user" | "assistant"; content: string }

/** Chat de teste com streaming SSE contra /v1/chat/completions. */
export default function Playground() {
  const { push } = useToast();
  const { data } = useQuery({ queryKey: ["models"], queryFn: () => api.get<ModelsResponse>("/api/models") });
  const [model, setModel] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [streaming, setStreaming] = useState(false);
  const abort = useRef<AbortController | null>(null);
  const chosen = model || data?.default_model || "";

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;
    const history: Msg[] = [...messages, { role: "user", content: text }];
    setMessages([...history, { role: "assistant", content: "" }]);
    setInput("");
    setStreaming(true);
    abort.current = new AbortController();

    try {
      const res = await fetch("/v1/chat/completions", {
        method: "POST",
        signal: abort.current.signal,
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ model: chosen, messages: history, stream: true }),
      });
      if (!res.ok || !res.body) throw new Error(`Erro ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") continue;
          const delta = JSON.parse(payload)?.choices?.[0]?.delta?.content;
          if (delta) {
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { role: "assistant", content: copy[copy.length - 1].content + delta };
              return copy;
            });
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") push((err as Error).message, "error");
    } finally {
      setStreaming(false);
      abort.current = null;
    }
  }

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col gap-4">
      <div className="card flex flex-wrap items-center gap-3 py-3">
        <select className="input max-w-xs" value={chosen} onChange={(e) => setModel(e.target.value)}>
          {data?.models.map((m) => <option key={m.name} value={m.name}>{m.name}</option>)}
        </select>
        <button className="btn-ghost" onClick={() => setMessages([])}>Limpar</button>
        {streaming && <button className="btn-danger" onClick={() => abort.current?.abort()}>Cancelar</button>}
      </div>

      <div className="card flex-1 space-y-4 overflow-y-auto">
        {messages.length === 0 && <p className="text-muted-foreground">Envie uma mensagem para testar o modelo.</p>}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <div className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
              m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
              {m.content || (streaming ? "..." : "")}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={send} className="flex gap-2">
        <input className="input" maxLength={8000} value={input} onChange={(e) => setInput(e.target.value)}
          placeholder="Digite sua mensagem..." />
        <button className="btn-primary" disabled={streaming}>Enviar</button>
      </form>
    </div>
  );
}
