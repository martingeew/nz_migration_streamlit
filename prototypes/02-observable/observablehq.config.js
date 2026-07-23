import {existsSync} from "node:fs";
import {fileURLToPath} from "node:url";

// ── Python interpreter ─────────────────────────────────────────────────────────
// Framework runs .py data loaders with `python3`, which does not exist on
// Windows. Point it at the repo venv instead, falling back to POSIX layout.
const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const venvWindows = `${repoRoot}.venv/Scripts/python.exe`;
const venvPosix = `${repoRoot}.venv/bin/python`;
const python = existsSync(venvWindows)
  ? venvWindows
  : existsSync(venvPosix)
    ? venvPosix
    : "python3";

export default {
  title: "Two migration stories in one line",
  root: "src",
  style: "style.css",
  pages: [],
  toc: false,
  sidebar: false,
  header: "",
  footer:
    "Prototype B of 3 — Observable Framework + Scrollama. Source: Statistics NZ ITM552301.",
  interpreters: {
    ".py": [python]
  }
};
