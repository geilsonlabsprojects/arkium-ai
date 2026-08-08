import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import Skeleton from "../components/Skeleton";
import { useToast } from "../components/Toast";

const FIELDS: { key: string; label: string; hint?: string }[] = [
  { key: "platform_name", label: "Nome da plataforma" },
  { key: "platform_description", label: "Descricao" },
  { key: "platform_logo", label: "Logo (URL)" },
  { key: "default_model", label: "Modelo padrao" },
  { key: "temperature", label: "Temperatura", hint: "0 a 2" },
  { key: "max_tokens", label: "Max tokens" },
  { key: "timeout", label: "Timeout (segundos)" },
  { key: "rate_limit_requests", label: "Rate limit - requisicoes" },
  { key: "rate_limit_window", label: "Rate limit - janela (s)" },
];

/** Configuracoes globais persistidas no banco. */
export default function SettingsPage() {
  const qc = useQueryClient();
  const { push } = useToast();
  const { data, isLoading } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<Record<string, string>>("/api/admin/settings") });
  const [form, setForm] = useState<Record<string, string>>({});

  useEffect(() => { if (data) setForm(data); }, [data]);

  const save = useMutation({
    mutationFn: () => api.put("/api/admin/settings", { values: form }),
    onSuccess: () => { push("Configuracoes salvas", "success"); void qc.invalidateQueries({ queryKey: ["settings"] }); },
    onError: (e: Error) => push(e.message, "error"),
  });

  if (isLoading) return <Skeleton className="h-64" />;

  return (
    <div className="card max-w-2xl space-y-4">
      {FIELDS.map((f) => (
        <div key={f.key}>
          <label className="label" htmlFor={f.key}>{f.label}</label>
          <input id={f.key} className="input" maxLength={300} value={form[f.key] ?? ""}
            onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
          {f.hint && <p className="mt-1 text-xs text-muted-foreground">{f.hint}</p>}
        </div>
      ))}
      <button className="btn-primary" onClick={() => save.mutate()} disabled={save.isPending}>
        {save.isPending ? "Salvando..." : "Salvar"}
      </button>
      <p className="text-xs text-muted-foreground">
        Porta, host, CORS e URLs do Ollama sao definidos no arquivo <code>.env</code> (exige reinicio).
      </p>
    </div>
  );
}
