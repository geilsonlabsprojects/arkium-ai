import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// O proxy evita CORS em desenvolvimento: o painel chama /api e /v1 no mesmo host.
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/v1": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
