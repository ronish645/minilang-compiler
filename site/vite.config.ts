import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served from https://<user>.github.io/minilang-compiler/ on GitHub Pages.
export default defineConfig({
  base: "/minilang-compiler/",
  plugins: [react(), tailwindcss()],
  // The compiler worker loads Pyodide with a dynamic import(), so build it as an ES module.
  worker: { format: "es" },
  // The playground's lazy chunk is mostly the CodeMirror editor; it loads only on that page.
  build: { chunkSizeWarningLimit: 800 },
});
