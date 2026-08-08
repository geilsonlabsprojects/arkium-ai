import { useQuery } from "@tanstack/react-query";
import { Activity, Boxes, Cpu, KeyRound, Timer, Users, Zap } from "lucide-react";
import {
  BarElement, CategoryScale, Chart as ChartJS, Filler, Legend, LineElement,
  LinearScale, PointElement, Tooltip,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import { api } from "../services/api";
import type { DashboardStats } from "../services/types";
import StatCard from "../components/StatCard";
import StatusDot from "../components/StatusDot";
import Skeleton from "../components/Skeleton";
import { compact } from "../lib/utils";
import { useAuth } from "../hooks/useAuth";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler, Tooltip, Legend);

/** Painel principal com metricas, graficos e saude dos servicos. */
export default function Dashboard() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: () => api.get<DashboardStats>("/api/admin/stats"),
    enabled: !!user?.is_admin,
    refetchInterval: 15000,
  });
  const { data: usage } = useQuery({
    queryKey: ["my-usage"],
    queryFn: () => api.get<Record<string, number>>("/api/admin/my-usage"),
  });

  if (!user?.is_admin) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Zap} label="Requisicoes" value={usage?.total_requests ?? 0} />
        <StatCard icon={Activity} label="Hoje" value={usage?.requests_today ?? 0} />
        <StatCard icon={Cpu} label="Tokens" value={compact(usage?.total_tokens ?? 0)} />
        <StatCard icon={KeyRound} label="Chaves ativas" value={usage?.active_keys ?? 0} />
      </div>
    );
  }

  if (isLoading || !data) {
    return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-28" />)}</div>;
  }

  const labels = data.daily_usage.map((d) => d.date.slice(5));

  return (
    <div className="space-y-6">
      <div className="card flex flex-wrap items-center gap-6">
        <StatusDot status={data.health.api} label="API" />
        <StatusDot status={data.health.database} label="Banco" />
        <StatusDot status={data.health.ollama} label="Ollama" />
        <span className="text-sm text-muted-foreground">Versao {data.health.version}</span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Users} label="Usuarios" value={data.total_users} />
        <StatCard icon={KeyRound} label="API Keys" value={data.total_api_keys} />
        <StatCard icon={Zap} label="Requisicoes" value={compact(data.total_requests)} hint={`${data.requests_today} hoje`} />
        <StatCard icon={Boxes} label="Modelos" value={data.models_available} />
        <StatCard icon={Timer} label="Tempo medio" value={`${data.avg_duration_ms.toFixed(0)} ms`} />
        <StatCard icon={Cpu} label="CPU" value={`${data.system.cpu_percent.toFixed(0)}%`} />
        <StatCard icon={Activity} label="RAM" value={`${data.system.memory_percent.toFixed(0)}%`}
          hint={`${data.system.memory_used_mb.toFixed(0)} / ${data.system.memory_total_mb.toFixed(0)} MB`} />
        <StatCard icon={Activity} label="Disco" value={`${data.system.disk_percent.toFixed(0)}%`}
          hint={`${data.system.disk_used_gb} / ${data.system.disk_total_gb} GB`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-semibold">Requisicoes (14 dias)</h2>
          <Line
            data={{
              labels,
              datasets: [{
                label: "Requisicoes",
                data: data.daily_usage.map((d) => d.requests),
                borderColor: "hsl(199 89% 55%)",
                backgroundColor: "hsla(199, 89%, 55%, .18)",
                fill: true, tension: 0.35,
              }],
            }}
            options={{ responsive: true, plugins: { legend: { display: false } } }}
          />
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">Modelos mais usados</h2>
          <Bar
            data={{
              labels: data.top_models.map((m) => m.model),
              datasets: [{ label: "Requisicoes", data: data.top_models.map((m) => m.requests), backgroundColor: "hsl(173 70% 45%)" }],
            }}
            options={{ responsive: true, plugins: { legend: { display: false } } }}
          />
        </div>
      </div>
    </div>
  );
}
