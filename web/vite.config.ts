import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// O painel é publicado no GitHub Pages em /labia/.
export default defineConfig({
  base: "/labia/",
  plugins: [react(), tailwindcss()],
});
