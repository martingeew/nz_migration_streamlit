<script>
  import {untrack} from "svelte";
  import * as d3 from "d3";
  // Static build-time data, so it is imported rather than passed as a prop.
  // Reading a prop during $state initialization triggers state_referenced_locally.
  import data from "../data/story.json";

  let {step} = $props();

  const MARGIN = {top: 16, right: 128, bottom: 28, left: 52};
  const MARGIN_NARROW = {top: 16, right: 66, bottom: 28, left: 42};
  const HEADER_H = 62;       // px reserved above the plot for title + subtitle
  const TWEEN_MS = 700;      // y-axis retarget
  const FADE_MS = 450;       // cross-fade between charts
  const LABEL_GAP = 13;      // minimum px between two right-edge labels
  // Thin bands lose their label rather than stack up in the right margin.
  // The real "_other" catch-all bands sit under 0.5% of the stack, while
  // every named band across every chart sits above 3.8% - a wide gap - so
  // one threshold well below that gap is enough, on both mobile and desktop.
  // A tighter mobile-only threshold (previously 0.04, before that 0.08) kept
  // clipping legitimate bands as their share drifted a few tenths of a point
  // release to release (age 65+ at 3.87%, UK at 3.97% both fell under 0.04
  // after the May 2026 data refresh) - the space this filter is protecting is
  // vertical label crowding, which the decluttering pass below already
  // handles, not something that needs a stricter cutoff on a narrow screen.
  const LABEL_MIN_SHARE = 0.015;
  const LABEL_MIN_SHARE_NARROW = 0.015;

  // Border closure, marked the same way the Quarto dashboard marks it.
  const BORDER_MARKS = [
    {month: "2020-03", label: "Border closed"},
    {month: "2022-08", label: null}
  ];

  let width = $state(900);
  let height = $state(520);

  const series = data.series.map((d) => ({...d, date: new Date(`${d.month}-01`)}));
  const last = series.at(-1);

  const activeStep = $derived(data.steps[step]);
  const chartId = $derived(activeStep.chart);
  const chart = $derived(data.charts[chartId]);
  const margin = $derived(width < 720 ? MARGIN_NARROW : MARGIN);
  const plotHeight = $derived(Math.max(200, height - HEADER_H));

  // ── Animated y-domain ────────────────────────────────────────────────────────
  // The point of this stack: the axis retargets and the bands grow into place
  // rather than snapping. Hand-rolled with d3.interpolate + requestAnimationFrame
  // so it does not depend on a specific Svelte motion API version.

  // The two bounds are held as plain numbers rather than one array in $state:
  // d3.interpolateArray returns the same mutated array on every call, which a
  // deep-proxied $state array does not see, and reading the array back inside
  // the effect that writes it makes the tween chase its own tail.
  let y0 = $state(data.charts[data.steps[0].chart].y[0]);
  let y1 = $state(data.charts[data.steps[0].chart].y[1]);
  const yDomain = $derived([y0, y1]);
  let frame = null;

  $effect(() => {
    const [t0, t1] = chart.y;
    const from0 = untrack(() => y0);
    const from1 = untrack(() => y1);
    const lo = d3.interpolateNumber(from0, t0);
    const hi = d3.interpolateNumber(from1, t1);
    const started = performance.now();

    cancelAnimationFrame(frame);
    const tick = (now) => {
      const eased = d3.easeCubicOut(Math.min(1, (now - started) / TWEEN_MS));
      y0 = lo(eased);
      y1 = hi(eased);
      if (eased < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frame);
  });

  // ── Scales ───────────────────────────────────────────────────────────────────

  const xScale = $derived(
    d3
      .scaleUtc()
      .domain(d3.extent(series, (d) => d.date))
      .range([margin.left, width - margin.right])
  );

  const yScale = $derived(
    d3
      .scaleLinear()
      .domain(yDomain)
      .range([plotHeight - margin.bottom, margin.top])
  );

  // ── Bands ────────────────────────────────────────────────────────────────────
  // "stack" runs the keys through d3.stack, bottom key first. "mirror" areas each
  // key from zero instead, so a series stored negative (departures) fills
  // downward and the two directions read against one baseline.

  const bands = $derived.by(() => {
    const keys = chart.keys;
    const area = d3
      .area()
      .x((d) => xScale(d.date))
      .curve(d3.curveMonotoneX);

    if (chart.mode === "mirror") {
      const zero = yScale(0);
      return keys.map((key) => ({
        key,
        path: area.y0(zero).y1((d) => yScale(d[key]))(series),
        mid: yScale(last[key] / 2),
        share: 1
      }));
    }

    const stacked = d3.stack().keys(keys)(series);
    const total = stacked.at(-1).at(-1)[1] || 1;
    return stacked.map((layer, i) => {
      const [lo, hi] = layer.at(-1);
      return {
        key: keys[i],
        path: area.y0((d, j) => yScale(layer[j][0])).y1((d, j) => yScale(layer[j][1]))(series),
        mid: yScale((lo + hi) / 2),
        share: (hi - lo) / total
      };
    });
  });

  const linePath = $derived(
    chart.line
      ? d3
          .line()
          .x((d) => xScale(d.date))
          .y((d) => yScale(d[chart.line]))
          .curve(d3.curveMonotoneX)(series)
      : null
  );

  // ── Outgoing chart ───────────────────────────────────────────────────────────
  // Only the active chart's paths are recomputed while the axis tweens. The
  // chart being left behind keeps the shapes it last had and fades out over
  // them, so a step change costs one extra render rather than one per frame for
  // every series in the file.

  let outgoing = $state(null);
  let lastId = null;
  let lastBands = null;
  let lastLine = null;
  let fadeTimer = null;

  // Declared before the snapshot effect below, so it still sees the previous
  // chart's shapes when the step changes. Svelte runs effects in creation order.
  $effect(() => {
    const id = chartId;
    if (lastId !== null && lastId !== id) {
      outgoing = {id: lastId, bands: lastBands, line: lastLine};
      clearTimeout(fadeTimer);
      fadeTimer = setTimeout(() => (outgoing = null), FADE_MS + 60);
    }
    lastId = id;
  });

  $effect(() => {
    lastBands = bands;
    lastLine = linePath;
  });

  // ── Right-edge labels ────────────────────────────────────────────────────────
  // Placed at the vertical midpoint of each band's last value, then decluttered
  // so thin neighbouring bands do not print on top of each other.
  //
  // A one-directional push (top to bottom) cascades: a cluster of three or four
  // close-valued bands drags every label below it down by one gap each, so the
  // last label can end up displaced by 30-40px from the band it names, even
  // past the axis it should sit beside. Two passes - push down from the top,
  // pull up from the bottom - then averaging the two spreads the cluster around
  // its true position instead of dragging it toward one end.

  const labels = $derived.by(() => {
    const minShare = width < 720 ? LABEL_MIN_SHARE_NARROW : LABEL_MIN_SHARE;
    const placed = bands
      .filter((b) => b.share >= minShare)
      .map((b) => ({key: b.key, y: b.mid}));

    if (chart.line) placed.push({key: chart.line, y: yScale(last[chart.line])});

    placed.sort((a, b) => a.y - b.y);

    const down = placed.map((p) => p.y);
    for (let i = 1; i < down.length; i += 1) {
      down[i] = Math.max(down[i], down[i - 1] + LABEL_GAP);
    }
    const up = placed.map((p) => p.y);
    for (let i = up.length - 2; i >= 0; i -= 1) {
      up[i] = Math.min(up[i], up[i + 1] - LABEL_GAP);
    }
    placed.forEach((p, i) => { p.y = (down[i] + up[i]) / 2; });

    return placed;
  });

  // ── Ticks and formatting ─────────────────────────────────────────────────────

  const xTicks = $derived(xScale.ticks(width < 720 ? 5 : 8));
  const yTicks = $derived(yScale.ticks(6));
  const formatTick = (v) => (Math.abs(v) >= 1000 ? `${d3.format(",.0f")(v / 1000)}k` : v);

  const highlighted = $derived(new Set(activeStep.highlight ?? []));
  const isDim = (key) => highlighted.size > 0 && !highlighted.has(key);
  const borderX = (month) => xScale(new Date(`${month}-01`));
</script>

<div class="chart" bind:clientWidth={width} bind:clientHeight={height}>
  <div class="chart-header" style:padding-left="{margin.left}px">
    {#key chartId}
      <h2 class="chart-title">{chart.title}</h2>
      <p class="chart-subtitle">{chart.subtitle}</p>
    {/key}
  </div>

  <svg {width} height={plotHeight} role="img" aria-label={chart.title}>
    <!-- y grid -->
    {#each yTicks as tick}
      <line class="grid" x1={margin.left} x2={width - margin.right} y1={yScale(tick)} y2={yScale(tick)} />
      <text class="tick" x={margin.left - 8} y={yScale(tick)} text-anchor="end" dy="0.32em">
        {formatTick(tick)}
      </text>
    {/each}

    <!-- border closure markers -->
    {#each BORDER_MARKS as mark}
      <line
        class="border-mark"
        x1={borderX(mark.month)}
        x2={borderX(mark.month)}
        y1={margin.top}
        y2={plotHeight - margin.bottom}
      />
      {#if mark.label}
        <text class="border-label" x={borderX(mark.month) + 5} y={margin.top + 10}>{mark.label}</text>
      {/if}
    {/each}

    <!-- the chart being scrolled away from: frozen shapes, fading out -->
    {#if outgoing}
      <g class="layer is-leaving">
        {#each outgoing.bands as band (band.key)}
          <path class="band" d={band.path} fill={data.colors[band.key]} />
        {/each}
        {#if outgoing.line}
          <path class="netline" d={outgoing.line} stroke={data.colors[data.charts[outgoing.id].line]} />
        {/if}
      </g>
    {/if}

    <!-- the active chart -->
    {#key chartId}
      <g class="layer is-entering">
        {#each bands as band (band.key)}
          <path class="band" class:dim={isDim(band.key)} d={band.path} fill={data.colors[band.key]} />
        {/each}
        {#if linePath}
          <path class="netline" class:dim={isDim(chart.line)} d={linePath} stroke={data.colors[chart.line]} />
        {/if}
      </g>
    {/key}

    <!-- zero baseline, over the areas so it stays readable -->
    <line class="zero" x1={margin.left} x2={width - margin.right} y1={yScale(0)} y2={yScale(0)} />

    <!-- x axis -->
    {#each xTicks as tick}
      <text class="tick" x={xScale(tick)} y={plotHeight - margin.bottom + 18} text-anchor="middle">
        {tick.getUTCFullYear()}
      </text>
    {/each}

    <!-- band labels -->
    {#key chartId}
      {#each labels as label (label.key)}
        <text
          class="band-label"
          class:dim={isDim(label.key)}
          x={width - margin.right + 8}
          y={label.y}
          fill={data.colors[label.key]}
          dy="0.32em"
        >
          {data.labels[label.key]}
        </text>
      {/each}
    {/key}
  </svg>
</div>

<style>
  .chart {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    /* Flex children default to min-width:auto, so the SVG would otherwise widen
       the column past the container and force a horizontal scrollbar. */
    min-width: 0;
  }

  .chart-header {
    height: 62px;
    flex: none;
  }

  .chart-title {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .chart-subtitle {
    font-size: 0.8rem;
    color: var(--muted);
    margin: 0.15rem 0 0;
  }

  /* Header lines and the whole incoming layer fade together, so a step that
     changes chart reads as one swap rather than several. */
  .chart-header :global(h2),
  .chart-header :global(p),
  .layer.is-entering {
    animation: fade-in 0.45s ease both;
  }

  .layer.is-leaving {
    animation: fade-out 0.45s ease forwards;
    pointer-events: none;
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes fade-out {
    from { opacity: 1; }
    to { opacity: 0; }
  }

  svg {
    overflow: visible;
  }

  /* The highlight: bands the commentary is not about drop back so the one it is
     about reads first. */
  .band {
    fill-opacity: 1;
    transition: fill-opacity 0.4s ease;
  }

  .band.dim {
    fill-opacity: 0.18;
  }

  .netline {
    fill: none;
    stroke-width: 2.5;
    transition: opacity 0.4s ease;
  }

  .netline.dim {
    opacity: 0.25;
  }

  .band-label {
    font-size: 0.78rem;
    font-weight: 600;
    transition: opacity 0.4s ease;
  }

  .band-label.dim {
    opacity: 0.3;
  }

  .grid {
    stroke: var(--grid);
    stroke-width: 1;
  }

  .zero {
    stroke: var(--zero);
    stroke-width: 1;
  }

  .border-mark {
    stroke: var(--zero);
    stroke-width: 1;
    stroke-dasharray: 2 3;
  }

  .border-label {
    font-size: 0.68rem;
    fill: var(--faint);
  }

  .tick {
    font-size: 0.72rem;
    fill: var(--tick);
  }
</style>
