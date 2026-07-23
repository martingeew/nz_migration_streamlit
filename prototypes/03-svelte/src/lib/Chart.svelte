<script>
  import * as d3 from "d3";
  // Static build-time module, so it is imported rather than passed as a prop.
  // Reading a prop during $state initialization triggers state_referenced_locally.
  import data from "../../../data/net_migration_citizenship.json";

  let {step} = $props();

  const SERIES_KEYS = ["total", "nz", "non_nz"];
  const MARGIN = {top: 24, right: 130, bottom: 32, left: 60};
  const TWEEN_MS = 700;

  let width = $state(900);
  let height = $state(520);

  const series = data.series.map((d) => ({...d, date: new Date(`${d.month}-01`)}));
  const activeStep = $derived(data.steps[step]);

  // ── Animated y-domain ────────────────────────────────────────────────────────
  // The whole point of this prototype: the axis retargets and the lines morph
  // rather than snapping. Hand-rolled with d3.interpolate + requestAnimationFrame
  // so it does not depend on a specific Svelte motion API version.

  function domainFor(visibleKeys) {
    const values = series.flatMap((d) => visibleKeys.map((k) => d[k]));
    const [lo, hi] = d3.extent(values);
    const pad = (hi - lo) * 0.12;
    return [lo - pad, hi + pad];
  }

  let yDomain = $state(domainFor(data.steps[0].visible));
  let frame = null;

  $effect(() => {
    const target = domainFor(activeStep.visible);
    const from = yDomain;
    const interpolate = d3.interpolateArray(from, target);
    const started = performance.now();

    cancelAnimationFrame(frame);
    const tick = (now) => {
      const t = Math.min(1, (now - started) / TWEEN_MS);
      yDomain = interpolate(d3.easeCubicOut(t));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frame);
  });

  // ── Scales and paths ─────────────────────────────────────────────────────────

  const xScale = $derived(
    d3
      .scaleUtc()
      .domain(d3.extent(series, (d) => d.date))
      .range([MARGIN.left, width - MARGIN.right])
  );

  const yScale = $derived(
    d3
      .scaleLinear()
      .domain(yDomain)
      .range([height - MARGIN.bottom, MARGIN.top])
  );

  const paths = $derived(
    Object.fromEntries(
      SERIES_KEYS.map((key) => [
        key,
        d3
          .line()
          .x((d) => xScale(d.date))
          .y((d) => yScale(d[key]))
          .curve(d3.curveMonotoneX)(series)
      ])
    )
  );

  const xTicks = $derived(xScale.ticks(8));
  const yTicks = $derived(yScale.ticks(6));

  // ── Focus annotation ─────────────────────────────────────────────────────────

  const focus = $derived(
    activeStep.focus ? data.annotations[activeStep.focus] : null
  );
  const focusPoint = $derived(
    focus ? series.find((d) => d.month === focus.month) : null
  );

  const formatValue = d3.format(",.0f");
  const formatTick = (v) => (Math.abs(v) >= 1000 ? `${d3.format(",.0f")(v / 1000)}k` : v);
</script>

<div class="chart" bind:clientWidth={width}>
  <svg {width} {height} role="img" aria-label={activeStep.title}>
    <!-- y grid -->
    {#each yTicks as tick}
      <line
        class="grid"
        x1={MARGIN.left}
        x2={width - MARGIN.right}
        y1={yScale(tick)}
        y2={yScale(tick)}
      />
      <text class="tick" x={MARGIN.left - 10} y={yScale(tick)} text-anchor="end" dy="0.32em">
        {formatTick(tick)}
      </text>
    {/each}

    <!-- zero line -->
    <line
      class="zero"
      x1={MARGIN.left}
      x2={width - MARGIN.right}
      y1={yScale(0)}
      y2={yScale(0)}
    />

    <!-- x axis -->
    {#each xTicks as tick}
      <text class="tick" x={xScale(tick)} y={height - MARGIN.bottom + 20} text-anchor="middle">
        {tick.getUTCFullYear()}
      </text>
    {/each}

    <!-- series: always in the DOM, faded in and out by step -->
    {#each SERIES_KEYS as key}
      {@const visible = activeStep.visible.includes(key)}
      <path
        class="series"
        class:hidden={!visible}
        d={paths[key]}
        stroke={data.colors[key]}
      />
      <text
        class="series-label"
        class:hidden={!visible}
        x={width - MARGIN.right + 8}
        y={yScale(series.at(-1)[key])}
        fill={data.colors[key]}
        dy="0.32em"
      >
        {data.labels[key]}
      </text>
    {/each}

    <!-- focus annotation -->
    {#if focusPoint && focus}
      <g
        class="focus"
        transform="translate({xScale(focusPoint.date)},{yScale(focusPoint[focus.series])})"
      >
        <circle r="6" fill={data.colors[focus.series]} stroke="white" stroke-width="2" />
        <text
          class="focus-value"
          fill={data.colors[focus.series]}
          text-anchor="middle"
          y={focus.value > 0 ? -32 : 30}
        >
          {formatValue(focus.value)}
        </text>
        <text
          class="focus-label"
          fill={data.colors[focus.series]}
          text-anchor="middle"
          y={focus.value > 0 ? -16 : 46}
        >
          {focus.label}
        </text>
      </g>
    {/if}
  </svg>
</div>

<style>
  .chart {
    width: 100%;
  }

  svg {
    overflow: visible;
  }

  .series {
    fill: none;
    stroke-width: 3;
    transition: opacity 0.45s ease;
  }

  .series-label {
    font-size: 0.8rem;
    font-weight: 600;
    transition: opacity 0.45s ease;
  }

  .hidden {
    opacity: 0;
  }

  .grid {
    stroke: #eee;
    stroke-width: 1;
  }

  .zero {
    stroke: #ccc;
    stroke-width: 1;
  }

  .tick {
    font-size: 0.72rem;
    fill: #888;
  }

  .focus-value {
    font-size: 1rem;
    font-weight: 700;
  }

  .focus-label {
    font-size: 0.78rem;
  }
</style>
