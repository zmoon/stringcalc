import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  publicDir: false,
  build: {
    outDir: resolve(__dirname, "../stringcalc/widget"),
    emptyOutDir: false,
    lib: {
      entry: resolve(__dirname, "src/entries/widgets-esm.ts"),
      formats: ["es"],
      fileName: () => "_bundle.js",
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
    sourcemap: false,
    minify: "esbuild",
  },
});
