import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/Toast";

/** Cadastro de novo usuario (o primeiro vira administrador). */
export default function Register() {
  const { register, user } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password.length < 8) return push("A senha precisa de ao menos 8 caracteres", "error");
    setLoading(true);
    try {
      await register(form.name.trim(), form.email.trim(), form.password);
      navigate("/", { replace: true });
    } catch (err) {
      push(err instanceof Error ? err.message : "Falha no cadastro", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={onSubmit} className="card w-full max-w-sm animate-fade-in">
        <h1 className="mb-6 text-center text-xl font-semibold">Criar conta</h1>
        <label className="label">Nome</label>
        <input className="input mb-3" required maxLength={120}
          value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <label className="label">E-mail</label>
        <input className="input mb-3" type="email" required maxLength={255}
          value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label className="label">Senha (min. 8)</label>
        <input className="input mb-5" type="password" required minLength={8} maxLength={128}
          value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="btn-primary w-full" disabled={loading}>{loading ? "Criando..." : "Criar conta"}</button>
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Ja tem conta? <Link to="/login" className="text-primary">Entrar</Link>
        </p>
      </form>
    </div>
  );
}
