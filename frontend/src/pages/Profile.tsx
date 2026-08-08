import { useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/Toast";

/** Edicao de perfil e troca de senha. */
export default function Profile() {
  const { user, refresh } = useAuth();
  const { push } = useToast();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [pwd, setPwd] = useState({ current_password: "", new_password: "" });

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.put("/api/users/me", { name, email });
      await refresh();
      push("Perfil atualizado", "success");
    } catch (err) { push((err as Error).message, "error"); }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/api/users/me/password", pwd);
      setPwd({ current_password: "", new_password: "" });
      push("Senha alterada", "success");
    } catch (err) { push((err as Error).message, "error"); }
  }

  return (
    <div className="grid max-w-3xl gap-4 md:grid-cols-2">
      <form onSubmit={saveProfile} className="card space-y-3">
        <h2 className="font-semibold">Perfil</h2>
        <div><label className="label">Nome</label>
          <input className="input" maxLength={120} value={name} onChange={(e) => setName(e.target.value)} /></div>
        <div><label className="label">E-mail</label>
          <input className="input" type="email" maxLength={255} value={email} onChange={(e) => setEmail(e.target.value)} /></div>
        <button className="btn-primary w-full">Salvar</button>
      </form>
      <form onSubmit={changePassword} className="card space-y-3">
        <h2 className="font-semibold">Alterar senha</h2>
        <div><label className="label">Senha atual</label>
          <input className="input" type="password" required value={pwd.current_password}
            onChange={(e) => setPwd({ ...pwd, current_password: e.target.value })} /></div>
        <div><label className="label">Nova senha (min. 8)</label>
          <input className="input" type="password" required minLength={8} value={pwd.new_password}
            onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })} /></div>
        <button className="btn-primary w-full">Alterar</button>
      </form>
    </div>
  );
}
