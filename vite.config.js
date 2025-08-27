import { fileURLToPath, URL } from "node:url";
import path from "node:path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import { glob } from "glob";

export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./static", import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      input: Object.fromEntries(
        glob.sync("./static/**/*.js").map((file) => [
          // This removes `static/` as well as the file extension
          // so ./static/js/index.js becomes js/index
          path.relative(
            "static",
            file.slice(0, file.length - path.extname(file).length)
          ),
          // This expands to absolute paths
          fileURLToPath(new URL(file, import.meta.url)),
        ])
      ),
    },
    manifest: true,
  },
});
