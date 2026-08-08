import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { cn } from "../lib/utils";

type Kind = "success" | "error" | "info";
interface Toast { id: number; message: string; kind: Kind }

const Ctx = createContext<{ push: (message: string, kind?: Kind) => void }>({ push: () => {} });

/** Notificacoes flutuantes simples, sem dependencia externa. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);

  const push = useCallback((message: string, kind: Kind = "info") => {
    const id = Date.now() + Math.random();
    setItems((prev) => [...prev, { id, message, kind }]);
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  return (
    <Ctx.Provider value={{ push }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={cn(
              "animate-fade-in rounded-xl border border-border bg-card px-4 py-3 text-sm shadow-lg",
              t.kind === "success" && "border-l-4 border-l-[hsl(var(--success))]",
              t.kind === "error" && "border-l-4 border-l-[hsl(var(--danger))]",
              t.kind === "info" && "border-l-4 border-l-primary",
            )}
          >
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export const useToast = () => useContext(Ctx);
