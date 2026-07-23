---
toc: false
---

<!--
No `theme:` here on purpose. Page-level `theme` and project-level `style` are
mutually exclusive in Framework; setting theme would drop style.css entirely.
The air theme is imported from within style.css instead.
-->


```js
import scrollama from "npm:scrollama";

const data = await FileAttachment("data/migration.json").json();
const series = data.series.map((d) => ({...d, date: new Date(`${d.month}-01`)}));
```

<div class="hero">
  <h1>Two migration stories in one line</h1>
  <p class="standfirst">
    New Zealand's net migration hit a record ${data.annotations.peak.value.toLocaleString()}
    in the year to ${data.annotations.peak.label}. The headline number hid two
    opposite movements underneath it.
  </p>
  <p class="kicker">Prototype B of 3 — Observable Framework + Scrollama. Scroll to advance.</p>
</div>

```js
// ── Graphic container ──────────────────────────────────────────────────────────
// Created as its own cell so the chart can be sized to the sticky column rather
// than to Framework's page-level `width` builtin. Using `width` here would size
// the SVG to the full page and let default.css scale it down, shrinking the
// chart and its type along with it.
const graphicEl = html`<div class="scrolly-graphic"></div>`;
const chartWidth = Generators.width(graphicEl);
```

```js
// ── Narrative steps ────────────────────────────────────────────────────────────
// Built as its own cell that does NOT reference `step`. Referencing `step` here
// would create a cycle — step depends on scrollama, scrollama depends on these
// elements existing — and scrollama would fail with "no step elements".
const narrative = html`<div class="scrolly-narrative">
  ${data.steps.map(
    (s) => html`<div class="scrolly-step">
      <h2>${s.title}</h2>
      <p>${s.body}</p>
    </div>`
  )}
</div>`;
```

```js
// ── Scroll state ───────────────────────────────────────────────────────────────
// Generators.observe turns scrollama callbacks into a reactive value. Every cell
// that references `step` re-runs when the active step changes.
const step = Generators.observe((notify) => {
  notify(0);

  let scroller;
  let raf;

  // Framework orders cells by dependency, not document position, so the
  // narrative element may not be attached to the document yet. Wait for it.
  const start = () => {
    if (!narrative.isConnected) {
      raf = requestAnimationFrame(start);
      return;
    }
    scroller = scrollama();
    scroller
      .setup({step: narrative.querySelectorAll(".scrolly-step"), offset: 0.6})
      .onStepEnter(({index}) => notify(index));
  };
  raf = requestAnimationFrame(start);

  const onResize = () => scroller?.resize();
  addEventListener("resize", onResize);

  return () => {
    cancelAnimationFrame(raf);
    removeEventListener("resize", onResize);
    scroller?.destroy();
  };
});
```

```js
// ── Chart ──────────────────────────────────────────────────────────────────────
const activeStep = data.steps[step];

// Fixed domain across all steps so the chart never jumps between transitions.
const yDomain = d3.extent(series.flatMap((d) => [d.total, d.nz, d.non_nz]));
const yPad = (yDomain[1] - yDomain[0]) * 0.12;

const focus = activeStep.focus ? data.annotations[activeStep.focus] : null;
const focusPoint = focus
  ? series.find((d) => d.month === focus.month)
  : null;

const chart = Plot.plot({
  height: 520,
  marginLeft: 56,
  marginRight: 120, // room for the direct series labels
  width: chartWidth || 640,
  y: {
    domain: [yDomain[0] - yPad, yDomain[1] + yPad],
    grid: true,
    tickFormat: "~s",
    label: null
  },
  x: {label: null},
  marks: [
    Plot.ruleY([0], {stroke: "#ccc"}),

    // One line per visible series
    ...activeStep.visible.map((key) =>
      Plot.line(series, {
        x: "date",
        y: key,
        stroke: data.colors[key],
        strokeWidth: 3,
        curve: "monotone-x"
      })
    ),

    // Direct labels instead of a legend
    ...activeStep.visible.map((key) =>
      Plot.text([series.at(-1)], {
        x: "date",
        y: key,
        text: () => data.labels[key],
        fill: data.colors[key],
        textAnchor: "start",
        dx: 8,
        fontWeight: 600
      })
    ),

    // Annotation dot and callout for the focused step
    focusPoint
      ? Plot.dot([focusPoint], {
          x: "date",
          y: focus.series,
          r: 6,
          fill: data.colors[focus.series],
          stroke: "white",
          strokeWidth: 2
        })
      : null,
    focusPoint
      ? Plot.text([focusPoint], {
          x: "date",
          y: focus.series,
          text: () => `${focus.value.toLocaleString()}\n${focus.label}`,
          fill: data.colors[focus.series],
          dy: focus.value > 0 ? -28 : 34,
          fontWeight: 600,
          lineHeight: 1.3
        })
      : null
  ]
});
```

<div class="scrolly">
  ${graphicEl}
  ${narrative}
</div>

```js
// Mount the chart into the sticky column. Replacing children (rather than
// re-rendering the container) keeps `graphicEl` stable so Generators.width
// keeps observing the same node.
graphicEl.replaceChildren(chart);
```

```js
// Highlight the active step by toggling a class on the existing nodes, rather
// than re-rendering the narrative. Keeps `narrative` independent of `step`.
narrative
  .querySelectorAll(".scrolly-step")
  .forEach((node, i) => node.classList.toggle("is-active", i === step));
```

<div class="outro">

## What this prototype shows

The chart is a single Plot cell that re-renders whenever `step` changes. Because
Plot rebuilds the SVG from scratch each time, series appear and disappear
instantly rather than animating. Smooth interpolation between steps would mean
dropping to D3 for the transitions, which is what prototype C does.

The upside is that data prep stayed in Python. `src/data/migration.json.py`
imports the same `build_payload()` the other two prototypes use, and Framework
runs it at build time.

<p class="data-source">Source: Statistics NZ ITM552301 — migrant arrivals and departures by citizenship. 12-month rolling sum.</p>

</div>
