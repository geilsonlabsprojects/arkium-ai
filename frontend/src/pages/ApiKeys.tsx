import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import type { ApiKey, ApiKeyCreated } from "../services/types";
import Modal from "../components/Modal";
import Skeleton from "../components/Skeleton";
import { useToast } from "../components/Toast";
import { formatDate } from "../lib/utils";

/** Gestao completa das chaves de API do usuario. */
export default function ApiKeys() {
  const qc = useQueryClient();
  const { push } = useToast();
  const [name, setName] = useState("");
  const [created, setCreated] = useState<ApiKeyCreated | null>(null);

  const { data, isLoading } = useQuery({ queryKey: ["keys"], queryFn: () => api.get<ApiKey[]>("/api/keys") });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["keys"] });

  const create = useMutation({
    mutationFn: () => api.post<ApiKeyCreated>("/api/keys", { name: name.trim() || "default" }),
    onSuccess: (key) => { setCreated(key); setName(""); void invalidate(); },
    onError: (e: Error) => push(e.message, "error"),
  });
  const revoke = useMutation({
    mutationFn: (id: number) => api.post(`/api/keys/${id}/revoke`),
    onSuccess: () => { push("Chave revogada", "success"); void invalidate(); },
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.del(`/api/keys/${id}`),
    onSuccess: () => { push("Chave excluida", "success"); void invalidate(); },
  });
  const rename = useMutation({
    mutationFn: ({ id, value }: { id: number; value: string }) => api.patch(`/api/keys/${id}`, { name: value }),
    onSuccess: () => { push("Chave renomeada", "success"); void invalidate(); },
  });

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap items-end gap-3">
        <div className="min-w-48 flex-1">
          <label className="label" htmlFor="keyname">Nome da nova chave</label>
          <input id="keyname" className="input" maxLength={120} value={name}
            onChange={(e) => setName(e.target.value)} placeholder="ex.: producao" />
        </div>
        <button className="btn-primary" onClick={() => create.mutate()} disabled={create.isPending}>
          {create.isPending ? "Criando..." : "Criar chave"}
        </button>
      </div>

      {isLoading ? <Skeleton className="h-40" /> : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-muted-foreground">
              <tr>
                <th className="p-3">Nome</th><th className="p-3">Prefixo</th><th className="p-3">Status</th>
                <th className="p-3">Requisicoes</th><th className="p-3">Ultimo uso</th><th className="p-3">IP</th>
                <th className="p-3">Criada</th><th className="p-3">Acoes</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((k) => (
                <tr key={k.id} className="border-b border-border/60 last:border-0">
                  <td className="p-3">{k.name}</td>
                  <td className="p-3 font-mono text-xs">{k.key_prefix}...</td>
                  <td className="p-3">
                    <span className={`badge ${k.is_active ? "bg-[hsl(var(--success))]/15 text-[hsl(var(--success))]" : "bg-muted text-muted-foreground"}`}>
                      {k.is_active ? "ativa" : "revogada"}
                    </span>
                  </td>
                  <td className="p-3">{k.request_count}</td>
                  <td className="p-3">{formatDate(k.last_used_at)}</td>
                  <td className="p-3">{k.last_used_ip ?? "-"}</td>
                  <td className="p-3">{formatDate(k.created_at)}</td>
                  <td className="flex flex-wrap gap-2 p-3">
                    <button className="btn-ghost px-2 py-1 text-xs" onClick={() => {
                      const value = prompt("Novo nome", k.name);
                      if (value) rename.mutate({ id: k.id, value });
                    }}>Renomear</button>
                    {k.is_active && <button className="btn-ghost px-2 py-1 text-xs" onClick={() => revoke.mutate(k.id)}>Revogar</button>}
                    <button className="btn-danger px-2 py-1 text-xs" onClick={() => confirm("Excluir esta chave?") && remove.mutate(k.id)}>Excluir</button>
                  </td>
                </tr>
              ))}
              {data?.length === 0 && <tr><td className="p-4 text-muted-foreground" colSpan={8}>Nenhuma chave criada.</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={!!created} title="Chave criada" onClose={() => setCreated(null)}>
        <p className="mb-3 text-sm text-muted-foreground">
          Copie agora: por seguranca, esta chave nao sera exibida novamente.
        </p>
        <code className="block break-all rounded-xl bg-muted p-3 text-sm">{created?.key}</code>
        <button className="btn-primary mt-4 w-full" onClick={() => {
          void navigator.clipboard.writeText(created?.key ?? ""); push("Chave copiada", "success");
        }}>Copiar</button>
      </Modal>
    </div>
  );
}
