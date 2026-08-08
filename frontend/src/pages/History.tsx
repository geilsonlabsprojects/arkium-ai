import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getToken } from "../services/api";
import type { Conversation } from "../services/types";
import Skeleton from "../components/Skeleton";
import { useToast } from "../components/Toast";
import { formatDate } from "../lib/utils";

/** Historico de conversas salvas: visualizar, exportar e apagar. */
export default function History() {
  const qc = useQueryClient();
  const { push } = useToast();
  const { data, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.get<Conversation[]>("/api/conversations"),
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.del(`/api/conversations/${id}`),
    onSuccess: () => { push("Conversa apagada", "success"); void qc.invalidateQueries({ queryKey: ["conversations"] }); },
  });

  async function exportConversation(id: number) {
    const res = await fetch(`/api/conversations/${id}/export`, { headers: { Authorization: `Bearer ${getToken()}` } });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `conversa-${id}.json`; a.click();
    URL.revokeObjectURL(url);
  }

  if (isLoading) return <Skeleton className="h-48" />;

  return (
    <div className="space-y-3">
      {data?.map((c) => (
        <div key={c.id} className="card flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium">{c.title}</p>
            <p className="text-xs text-muted-foreground">{c.model ?? "-"} - {formatDate(c.updated_at)}</p>
          </div>
          <div className="flex gap-2">
            <button className="btn-ghost text-xs" onClick={() => void exportConversation(c.id)}>Exportar</button>
            <button className="btn-danger text-xs" onClick={() => confirm("Apagar?") && remove.mutate(c.id)}>Apagar</button>
          </div>
        </div>
      ))}
      {data?.length === 0 && <p className="text-muted-foreground">Nenhuma conversa salva.</p>}
    </div>
  );
}
