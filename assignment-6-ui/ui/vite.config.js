import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on :5173; the FastAPI backend runs on :8000 (see src/api.js).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
