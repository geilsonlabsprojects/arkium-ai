import { cn } from "../lib/utils";

/** Indicador colorido de status online/offline. */
export default function StatusDot({ status, label }: { status: string; label: string }) {
  const online = status === "online" || status === "ok";
  return (
    <span className="inline-flex items-center gap-2 text-sm">
      <span className={cn("h-2.5 w-2.5 rounded-full", online ? "bg-[hsl(var(--success))]" : "bg-[hsl(var(--danger))]")} />
      {label}: <strong className="font-medium">{status}</strong>
    </span>
  );
}
