import { cn } from "../lib/utils";

/** Placeholder de carregamento. */
export default function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton h-4 w-full", className)} />;
}
