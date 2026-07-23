# Scrollytelling prototypes

Three stacks, one story, built to compare before committing to a rebuild of the
public dashboard.

The story is the same in all three: **net migration by citizenship**, a sticky
chart with five steps. Total line, annotate the 2023 peak, split into NZ vs
non-NZ citizens, highlight the NZ-citizen trough, return to total with the
latest reading. That covers the three moves that matter in a data story: reveal
a series, retarget the axes, move an annotation.

All three read the **same** JSON, so the numbers are identical and only the
rendering differs.

## Setup

```bash
# Shared data (run this first — the other three depend on it)
.venv/Scripts/python prototypes/export_prototype_data.py

# A — Quarto + Closeread
.venv/Scripts/python prototypes/01-closeread/make_charts.py
cd prototypes/01-closeread && quarto preview index.qmd

# B — Observable Framework + Scrollama
cd prototypes/02-observable && npm install && npm run dev

# C — Vite + Svelte + Scrollama + D3
cd prototypes/03-svelte && npm install && npm run dev
```

## Scorecard

| | A — Closeread | B — Observable Framework | C — Svelte |
|---|---|---|---|
| **Code written** | 1 `.qmd` + 130-line Python chart script | 1 `.md` (~170 lines) + 25-line data loader | 4 files, ~450 lines |
| **Dependencies** | Quarto extension, no npm | 3 npm packages | 4 npm packages |
| **Data prep** | Python (Plotly figures) | **Python** (build-time loader) | Python (static JSON import) |
| **Chart library** | Plotly | Observable Plot | hand-rolled D3 + SVG |
| **Transitions** | cross-fade between 5 pre-rendered charts | instant re-render | **true tween** — axis interpolates, lines morph |
| **Mobile** | works, but needed ~30 lines of override CSS | worked first try | worked after one `min-width: 0` |
| **Deploys to `docs/`** | yes, same as current site | static `dist/`, new pipeline | static `dist/`, new pipeline |
| **Payload** | 5 Plotly fragments + Plotly CDN (~1MB) | 591 kB imports + 46 kB data | 138 kB JS total (48 kB gzipped) |

## What each one felt like

**A — Closeread.** Lowest lift by a wide margin, and it slots into the existing
build with no new tooling. The catch is that it swaps between five separately
rendered charts rather than animating one, so transitions are cross-fades. The
chart also has to be generated five times, which means five copies of the same
data in the payload. Mobile needed real fighting: Closeread keeps its sticky
column at ~700px on narrow viewports, and the obvious fix (`overflow-x: hidden`)
silently disables `position: sticky` on every descendant. Use `overflow-x: clip`.

**B — Observable Framework.** The best fit for a Python-first workflow. The data
loader at `02-observable/src/data/migration.json.py` imports the same
`build_payload()` the other two use and runs at build time, so data prep never
leaves Python. Two gotchas cost time: page-level `theme:` and project-level
`style:` are mutually exclusive (setting `theme` silently drops your stylesheet),
and Framework's `width` builtin is the *page* width, not your container's, which
silently scales the chart down. Use `Generators.width(element)` instead.

**C — Svelte.** The only one where the chart genuinely animates. All three series
stay in the DOM and the y-domain is interpolated with `d3.interpolateArray`
inside a `requestAnimationFrame` loop, so the axis retargets and the lines morph
between steps. That is the thing the other two cannot do without dropping to
this level anyway. The cost is that the axes, grid, ticks, labels, and annotation
are all hand-drawn SVG — roughly 200 lines that Plotly and Plot give you free.

## Recommendation

If the goal is one polished flagship story where the chart animation is the
point, **C**. If the goal is publishing migration stories regularly and keeping
data prep in Python, **B** — it is the best ratio of control to effort, and the
Python data loader means the existing pipeline carries over. **A** is worth it
only if avoiding npm entirely matters more than the transitions do.

## Windows notes

- Framework runs `.py` data loaders with `python3`, which does not exist on
  Windows. `02-observable/observablehq.config.js` pins the interpreter to the
  repo venv via the `interpreters` option.
- Everything else runs unmodified on Node 22 / npm 10 / Quarto 1.6.

## Verified

All three were driven in a real browser at 1440×900 and 390×844:

- Five steps fire in order on wheel scroll, in all three.
- Chart content matches the step (peak 135,529 Oct 2023; trough -45,915 Apr 2024;
  latest 24,250 Mar 2026).
- No horizontal overflow at either viewport.

Note that scrollama uses IntersectionObserver, so large instant scroll jumps
(`window.scrollTo`) can skip steps. Incremental scrolling is the accurate test.
