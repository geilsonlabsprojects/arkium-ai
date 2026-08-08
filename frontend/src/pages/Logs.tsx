import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import type { RequestLog } from "../services/types";
import Skeleton from "../components/Skeleton";
import { useToast } from "../components/Toast";
import { formatDate } from "../lib/utils";

/** Tabela de logs de requisicao com filtro de erros e limpeza. */
export default function Logs() {
  const qc = useQueryClient();
  const { push } = useToast();
  const [onlyErrors, setOnlyErrors] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["logs", onlyErrors],
    queryFn: () => api.get<RequestLog[]>(`/api/admin/logs?limit=200&only_errors=${onlyErrors}`),
    refetchInterval: 20000,
  });
  const clear = useMutation({
    mutationFn: () => api.del("/api/admin/logs"),
    onSuccess: () => { push("Logs limpos", "success"); void qc.invalidateQueries({ queryKey: ["logs"] }); },
  });

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={onlyErrors} onChange={(e) => setOnlyErrors(e.target.checked)} />
          Somente erros
        </label>
        <button className="btn-danger text-xs" onClick={() => confirm("Limpar todos os logs?") && clear.mutate()}>
          Limpar logs
        </button>
      </div>
      {isLoading ? <Skeleton className="h-64" /> : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-muted-foreground">
              <tr><th className="p-3">Data</th><th className="p-3">Endpoint</th><th className="p-3">Modelo</th>
                <th className="p-3">Status</th><th className="p-3">Tempo</th><th className="p-3">Tokens</th>
                <th className="p-3">IP</th><th className="p-3">Erro</th></tr>
            </thead>
            <tbody>
              {data?.map((l) => (
                <tr key={l.id} className="border-b border-border/60 last:border-0">
                  <td className="p-3 whitespace-nowrap">{formatDate(l.created_at)}</td>
                  <td className="p-3 font-mono text-xs">{l.endpoint}</td>
                  <td className="p-3">{l.model ?? "-"}</td>
                  <td className="p-3">{l.status_code}</td>
                  <td className="p-3">{l.duration_ms.toFixed(0)} ms</td>
                  <td className="p-3">{l.total_tokens}</td>
                  <td className="p-3">{l.ip_address ?? "-"}</td>
                  <td className="max-w-64 truncate p-3 text-[hsl(var(--danger))]">{l.error ?? ""}</td>
                </tr>
              ))}
              {data?.length === 0 && <tr><td className="p-4 text-muted-foreground" colSpan={8}>Sem registros.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
