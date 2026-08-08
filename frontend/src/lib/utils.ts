import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Junta classes Tailwind resolvendo conflitos. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formata data ISO para o padrao brasileiro. */
export function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("pt-BR");
}

/** Abrevia numeros grandes (1.2k, 3.4M). */
export function compact(n: number) {
  return new Intl.NumberFormat("pt-BR", { notation: "compact" }).format(n);
}
