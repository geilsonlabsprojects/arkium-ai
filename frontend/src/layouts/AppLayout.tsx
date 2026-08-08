import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity, BookOpen, Boxes, KeyRound, LayoutDashboard, LogOut, MessageSquare,
  Moon, ScrollText, Settings, Sun, User as UserIcon, Users as UsersIcon,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { api } from "../services/api";
import { cn } from "../lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, admin: false },
  { to: "/playground", label: "Playground", icon: MessageSquare, admin: false },
  { to: "/models", label: "Modelos", icon: Boxes, admin: false },
  { to: "/keys", label: "API Keys", icon: KeyRound, admin: false },
  { to: "/history", label: "Historico", icon: ScrollText, admin: false },
  { to: "/monitoring", label: "Monitoramento", icon: Activity, admin: true },
  { to: "/logs", label: "Logs", icon: ScrollText, admin: true },
  { to: "/users", label: "Usuarios", icon: UsersIcon, admin: true },
  { to: "/settings", label: "Configuracoes", icon: Settings, admin: true },
  { to: "/docs", label: "Documentacao", icon: BookOpen, admin: false },
];

/** Layout com sidebar responsiva, topo e area de conteudo. */
export default function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const { data: platform } = useQuery({
    queryKey: ["platform"],
    queryFn: () => api.get<{ name: string; version: string }>("/api/platform"),
  });

  const items = NAV.filter((i) => !i.admin || user?.is_admin);

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          "fixed inset-y-0 z-40 flex w-64 flex-col border-r border-border bg-card transition-transform md:static md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <img src="/logo.svg" alt="Logo" className="h-8 w-8" />
          <div>
            <p className="font-semibold leading-tight">{platform?.name ?? "Arkium AI"}</p>
            <p className="text-xs text-muted-foreground">v{platform?.version ?? "1.0.0"}</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition",
                  isActive ? "bg-primary/10 font-medium text-primary" : "text-muted-foreground hover:bg-muted",
                )
              }
            >
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-3">
          <NavLink to="/profile" className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm hover:bg-muted">
            <UserIcon size={18} /> {user?.name || user?.email}
          </NavLink>
          <button
            className="mt-1 flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
            onClick={() => { logout(); navigate("/login", { replace: true }); }}
          >
            <LogOut size={18} /> Sair
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-card/60 px-4 py-3 backdrop-blur">
          <button className="btn-ghost md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Menu">Menu</button>
          <div className="hidden text-sm text-muted-foreground md:block">
            API local compativel com a OpenAI - <code className="rounded bg-muted px-1.5 py-0.5">/v1</code>
          </div>
          <button className="btn-ghost" onClick={toggle} aria-label="Alternar tema">
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </header>
        <main className="flex-1 overflow-x-hidden p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
