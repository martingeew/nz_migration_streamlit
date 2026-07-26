import {defineConfig} from "vite";
import {svelte} from "@sveltejs/vite-plugin-svelte";

// Local preview only. This repository's GitHub Pages site already serves the
// Quarto dashboard from /docs, so this story is not deployed and `base` stays
// at the root. To publish it, set base to "/<repo>/" and add the skill's
// .github/workflows/deploy.yml.
export default defineConfig({
  base: "/",
  plugins: [svelte()]
});
