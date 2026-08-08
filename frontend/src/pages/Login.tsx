import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../components/Toast";

/** Tela de login. */
export default function Login() {
  const { login, user } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      push(err instanceof Error ? err.message : "Falha no login", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={onSubmit} className="card w-full max-w-sm animate-fade-in">
        <img src="/logo.svg" alt="" className="mx-auto mb-4 h-12 w-12" />
        <h1 className="mb-1 text-center text-xl font-semibold">Entrar</h1>
        <p className="mb-6 text-center text-sm text-muted-foreground">Acesse o painel da plataforma</p>
        <label className="label" htmlFor="email">E-mail</label>
        <input id="email" className="input mb-3" type="email" required maxLength={255}
          value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="label" htmlFor="password">Senha</label>
        <input id="password" className="input mb-5" type="password" required maxLength={128}
          value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="btn-primary w-full" disabled={loading}>{loading ? "Entrando..." : "Entrar"}</button>
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Nao tem conta? <Link to="/register" className="text-primary">Cadastre-se</Link>
        </p>
      </form>
    </div>
  );
}
