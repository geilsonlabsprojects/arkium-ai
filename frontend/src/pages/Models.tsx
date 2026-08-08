import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import type { ModelsResponse } from "../services/types";
import Skeleton from "../components/Skeleton";
import { useToast } from "../components/Toast";
import { useAuth } from "../hooks/useAuth";
import { formatDate } from "../lib/utils";

/** Lista os modelos detectados no Ollama e permite definir o padrao. */
export default function Models() {
  const { user } = useAuth();
  const { push } = useToast();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["models"], queryFn: () => api.get<ModelsResponse>("/api/models") });

  const setDefault = useMutation({
    mutationFn: (model: string) => api.post(`/api/models/default?model=${encodeURIComponent(model)}`),
    onSuccess: () => { push("Modelo padrao atualizado", "success"); void qc.invalidateQueries({ queryKey: ["models"] }); },
    onError: (e: Error) => push(e.message, "error"),
  });

  if (isLoading) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-4">
      {!data?.online && (
        <div className="card border-l-4 border-l-[hsl(var(--danger))]">
          Ollama offline. Inicie o Ollama e rode <code className="rounded bg-muted px-1">ollama pull llama3.2</code>.
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data?.models.map((m) => (
          <div key={m.name} className="card animate-fade-in">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium">{m.name}</p>
                <p className="text-xs text-muted-foreground">
                  {m.details?.parameter_size ?? "-"} - {m.details?.quantization_level ?? "-"}
                </p>
              </div>
              {data.default_model === m.name && <span className="badge bg-primary/10 text-primary">padrao</span>}
            </div>
            <p className="mt-3 text-xs text-muted-foreground">Atualizado: {formatDate(m.modified_at)}</p>
            {user?.is_admin && data.default_model !== m.name && (
              <button className="btn-ghost mt-3 w-full" onClick={() => setDefault.mutate(m.name)}>
                Definir como padrao
              </button>
            )}
          </div>
        ))}
        {data?.models.length === 0 && <p className="text-muted-foreground">Nenhum modelo instalado.</p>}
      </div>
    </div>
  );
}
