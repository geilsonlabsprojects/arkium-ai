import type { LucideIcon } from "lucide-react";

/** Cartao de metrica do dashboard. */
export default function StatCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="card animate-fade-in transition hover:shadow-md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
          {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
        </div>
        <span className="rounded-xl bg-primary/10 p-2 text-primary">
          <Icon size={20} />
        </span>
      </div>
    </div>
  );
}
