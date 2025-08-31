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
  // Optional: Silence Sass deprecation warnings. # https://getbootstrap.com/docs/5.3/getting-started/vite/
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: [
          "import",
          "mixed-decls",
          "color-functions",
          "global-builtin",
        ],
      },
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
    outDir: "static",
    emptyOutDir: false, // We don't want to delete everything in static/
    manifest: true,
    assetsDir: "__vite__",
  },
});
