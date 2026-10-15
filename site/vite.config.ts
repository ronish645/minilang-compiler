import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served from https://<user>.github.io/minilang-compiler/ on GitHub Pages.
export default defineConfig({
  base: "/minilang-compiler/",
  plugins: [react(), tailwindcss()],
});
