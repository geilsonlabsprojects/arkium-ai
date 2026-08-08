import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import type { HealthStatus, SystemStats } from "../services/types";
import StatusDot from "../components/StatusDot";
import Skeleton from "../components/Skeleton";

interface Snapshot {
  system: SystemStats;
  health: HealthStatus;
  running_models: { name: string; size_vram?: number }[];
  ollama_hosts: string[];
  timestamp: string;
}

/** Monitoramento em tempo real (atualiza a cada 5s). */
export default function Monitoring() {
  const { data, isLoading } = useQuery({
    queryKey: ["monitoring"],
    queryFn: () => api.get<Snapshot>("/api/admin/monitoring"),
    refetchInterval: 5000,
  });

  if (isLoading || !data) return <Skeleton className="h-64" />;

  const bars = [
    { label: "CPU", value: data.system.cpu_percent },
    { label: "Memoria", value: data.system.memory_percent },
    { label: "Disco", value: data.system.disk_percent },
  ];

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap gap-6">
        <StatusDot status={data.health.api} label="API" />
        <StatusDot status={data.health.database} label="Banco" />
        <StatusDot status={data.health.ollama} label="Ollama" />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {bars.map((b) => (
          <div key={b.label} className="card">
            <p className="mb-2 text-sm text-muted-foreground">{b.label}</p>
            <p className="mb-2 text-2xl font-semibold">{b.value.toFixed(0)}%</p>
            <div className="h-2 w-full rounded-full bg-muted">
              <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${Math.min(b.value, 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="card">
        <h2 className="mb-3 font-semibold">Modelos carregados em memoria</h2>
        {data.running_models.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhum modelo carregado no momento.</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {data.running_models.map((m) => <li key={m.name}>{m.name}</li>)}
          </ul>
        )}
        <p className="mt-4 text-xs text-muted-foreground">Servidores Ollama: {data.ollama_hosts.join(", ")}</p>
      </div>
    </div>
  );
}
