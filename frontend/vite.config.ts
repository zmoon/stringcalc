import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig(({ command }) => ({
  base: "./",
  publicDir: command === "serve" ? "public" : false,
  build: {
    outDir: "../stringcalc/_web",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        misc: resolve(__dirname, "misc.html"),
      },
    },
  },
  worker: {
    format: "es",
  },
  test: {
    environment: "happy-dom",
  },
}));
