import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import type { User } from "../services/types";
import Skeleton from "../components/Skeleton";
import { useToast } from "../components/Toast";
import { formatDate } from "../lib/utils";

/** Administracao de usuarios (somente admin). */
export default function Users() {
  const qc = useQueryClient();
  const { push } = useToast();
  const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: () => api.get<User[]>("/api/users") });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["users"] });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) => api.patch(`/api/users/${id}/active?active=${active}`),
    onSuccess: () => { push("Status atualizado", "success"); void invalidate(); },
    onError: (e: Error) => push(e.message, "error"),
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.del(`/api/users/${id}`),
    onSuccess: () => { push("Usuario removido", "success"); void invalidate(); },
    onError: (e: Error) => push(e.message, "error"),
  });

  if (isLoading) return <Skeleton className="h-48" />;

  return (
    <div className="card overflow-x-auto p-0">
      <table className="w-full text-sm">
        <thead className="border-b border-border text-left text-muted-foreground">
          <tr><th className="p-3">Nome</th><th className="p-3">E-mail</th><th className="p-3">Perfil</th>
            <th className="p-3">Status</th><th className="p-3">Ultimo login</th><th className="p-3">Acoes</th></tr>
        </thead>
        <tbody>
          {data?.map((u) => (
            <tr key={u.id} className="border-b border-border/60 last:border-0">
              <td className="p-3">{u.name}</td>
              <td className="p-3">{u.email}</td>
              <td className="p-3">{u.is_admin ? "admin" : "usuario"}</td>
              <td className="p-3">{u.is_active ? "ativo" : "inativo"}</td>
              <td className="p-3">{formatDate(u.last_login_at)}</td>
              <td className="flex gap-2 p-3">
                <button className="btn-ghost px-2 py-1 text-xs" onClick={() => toggle.mutate({ id: u.id, active: !u.is_active })}>
                  {u.is_active ? "Desativar" : "Ativar"}
                </button>
                <button className="btn-danger px-2 py-1 text-xs" onClick={() => confirm("Excluir usuario?") && remove.mutate(u.id)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
