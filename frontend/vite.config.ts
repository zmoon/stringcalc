import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    outDir: "dist/app",
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
});
