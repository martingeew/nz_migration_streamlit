# Who is actually arriving in New Zealand

A scroll-driven data story on NZ migration: five stacked-area charts, nine steps, one
chart pinned to the top of the screen while the commentary scrolls past underneath it.

Built from the `scrollytelling-starter` Claude skill as the worked example for
`blog/2026-07-23_nyt-scrollytelling-python-stack.md`. Stack is Vite + Svelte 5 +
Scrollama + D3, with all data prep in Python.

## Run it

```bash
python ../scrolly/data/build.py   # from the repo root: rebuilds src/data/story.json
npm install
npm run dev                       # http://localhost:5173
```

`src/data/story.json` is committed, so `npm install && npm run dev` works on a fresh
clone without running Python first. Rebuild it whenever the Stats NZ interim pkl files
are refreshed.

On Windows, run the builder with the repo venv:

```bash
.venv/Scripts/python scrolly/data/build.py
```

## Not deployed

This repository's GitHub Pages site already serves the Quarto dashboard from `/docs`, so
the skill's `.github/workflows/deploy.yml` was deliberately left out — wiring it up means
switching Pages to "GitHub Actions" as its source, which would take the dashboard down.
To publish this story somewhere, copy `scrolly/` into its own repo, set `base` in
`vite.config.js` to `"/<repo>/"`, and add the workflow back from
`blog/scrollytelling-starter/templates/.github/workflows/deploy.yml`.

## What the skill gave you, and what it did not

Straight from the templates, unedited:

| File | Note |
|---|---|
| `src/lib/Scrolly.svelte` | The scroll engine. Only its stylesheet changed, not its logic. |
| `src/main.js`, `src/app.css` | Untouched. |
| `src/styles/minimalist-dark.css` | Untouched. The white theme is still here; swap the import in `App.svelte` to see it. |
| `package.json`, `index.html` | Name and `<title>` only. |

Hand-edited, and why:

- **`data/build.py`** — the skill ships an example builder; this one reads the repo's
  interim pkl files through `src/dashboard/data_loader.py` and emits 25 series across
  five charts. Every number quoted in the commentary is computed here rather than typed,
  so the prose cannot drift from the data.
- **`src/lib/Chart.svelte`** — rewritten from an animated line chart to stacked areas
  with `d3.stack`, a mirrored mode for the arrivals-above / departures-below chart, and
  band highlighting. The skill's tweened y-domain survived the rewrite and is what makes
  the axis retarget between charts instead of snapping.
- **`src/lib/Scrolly.svelte`** — the template floats translucent narrative cards over a
  full-height sticky chart. Here the graphic pins to the top `--chart-h` and each step is
  a tall scroll zone whose text is itself sticky, parked `--stick-gap` below the chart for
  the length of that zone. So every step is read in the same place, directly under the
  graphic it describes, and the step being read never covers the chart. When its zone runs
  out the text climbs over the chart and dissolves (`paintExit()`) rather than being
  clipped behind an opaque edge. The fade has to be driven by scroll position, not by
  active state: scrollama keeps a step active until the next one triggers, so an active
  step keeps climbing long after it has passed the chart's lower edge.

  Four numbers shape the scroll feel, all on `.scrolly`: `--chart-h` (how much of the
  screen the chart keeps), `--stick-gap` (where the text parks below it), `--step-read`
  (how long it stays parked) and `--exit-travel` (how far it climbs while dissolving,
  which is also the gap that opens before the next step's text appears).
- **`data/story.schema.md`** — documents the four contract extensions (`charts`,
  `steps[].chart`, `steps[].highlight`, `meta.sources`/`meta.notes`).

Two things cost real time and are worth knowing before you start:

1. **Do not hold the tweening y-domain in a `$state` array.** `d3.interpolateArray`
   returns the same mutated array every frame, which a deep-proxied Svelte array does not
   register, and reading that state back inside the effect that writes it makes the tween
   chase its own tail. The axis ran away to -700k before this was split into two plain
   numbers with `untrack`. See the comment in `Chart.svelte`.
2. **Scrollama's instance method is `offset()`, not `offsetTrigger()`.** The trigger
   point has to move with the chart height when the layout switches to the phone
   breakpoint, and the wrong name fails silently until you resize the window.
3. **Gate the exit fade on the chart having actually pinned.** The first step sits flush
   beneath the graphic in document flow, so before the graphic sticks it is already inside
   the fade zone and never reaches full strength. `paintExit()` checks
   `box.top <= 1` first.
4. **Park the text with `position: sticky`; a scrollama offset alone will not do it.**
   Triggering a step "just below the chart" only sets where it *starts*; it then keeps
   scrolling, so it is only in the right place for an instant. Worse, the first step gets
   a different gap from the rest (0px against 144px here) because it activates before the
   graphic has pinned and so rides down with it. Making each step a tall zone with sticky
   text inside gives every step the same resting position and a long readable window.
   `--chart-h` and `--stick-gap` are the single source of truth: the graphic height, the
   sticky offset and the scrollama trigger are all derived from them, the last two by
   reading the custom properties back with `getComputedStyle`.
5. **Sticky text needs explicit room to leave, or consecutive steps sit flush.** One
   zone's bottom is the next zone's top, so the moment a parked step releases, the next
   step's text is arriving at exactly that point: the two end up stacked with no gap.
   A `margin-bottom: var(--exit-travel)` on the sticky element releases it that much
   earlier (a sticky element is held inside its containing block by its *margin* box), so
   it climbs away while the next text is still `--exit-travel` below the fold. Zone height
   is then `--step-read + --exit-travel`.
