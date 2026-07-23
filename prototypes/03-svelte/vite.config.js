import {defineConfig} from "vite";
import {svelte} from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    // The shared JSON lives in prototypes/data/, outside this project root.
    // Importing it directly keeps a single source of truth with no copy step.
    fs: {allow: [".."]}
  }
});
