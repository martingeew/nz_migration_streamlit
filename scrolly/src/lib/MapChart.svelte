<script>
  import * as d3 from "d3";
  // Static build-time data, imported rather than passed as props. Geometry lives
  // in its own file: it is far larger than the story and never read by eye.
  import data from "../data/story.json";
  import maps from "../data/maps.json";

  let {step} = $props();

  const HEADER_H = 62;   // px reserved above the map for title + subtitle
  const PAD = 10;
  // Gutter kept clear on each side for annotation labels. The projection is fitted
  // inside what is left, so a label never has to sit on top of the map.
  const GUTTER = 124;
  const GUTTER_NARROW = 78;
  // Room reserved at the bottom of the plot for the legend, so it never has to
  // share space with the map. Reserved whether or not the legend is currently
  // shown - see the note on `projection` below for why.
  const LEGEND_H = 50;
  // The left rail every other block on the page sits on: Chart.svelte's margin,
  // the narrative's padding, the hero. The title belongs on this, NOT on the
  // gutter, which is only about where annotation labels may go.
  const RAIL = 52;
  const RAIL_NARROW = 42;
  const NO_DATA = "#1B2026";

  let width = $state(900);
  let height = $state(520);

  const activeStep = $derived(data.steps[step]);
  const chartId = $derived(activeStep.chart);
  const chart = $derived(data.charts[chartId]);
  const geo = $derived(maps[chart.map]);
  const plotHeight = $derived(Math.max(220, height - HEADER_H));
  const narrow = $derived(width < 720);
  const gutter = $derived(narrow ? GUTTER_NARROW : GUTTER);
  const rail = $derived(narrow ? RAIL_NARROW : RAIL);

  // One label size at every width. These track the font sizes in the stylesheet:
  // LINE_H is the leading, CHAR_W the average glyph width used to reserve room.
  const LINE_H = 14;
  const LABEL_SLOT = LINE_H * 3 + 13;  // three lines plus breathing room
  const CHAR_W = 6.2;

  const color = $derived(
    d3.scaleLinear().domain(chart.scale.domain).range(chart.scale.range).clamp(true)
  );

  // ── Projection ───────────────────────────────────────────────────────────────
  // Fitted to the features worth framing, not all of them: Great Barrier sits 60km
  // off Auckland and would shrink the city to a corner if it drove the fit. It is
  // still drawn and coloured, just allowed to fall outside the frame.

  /** What the projection should frame: an explicit lon/lat window when the chart
   *  gives one, otherwise the features worth showing. */
  const fitTarget = $derived.by(() => {
    if (chart.fitBBox) {
      const [[west, south], [east, north]] = chart.fitBBox;
      // Clockwise, like every other ring here: wound the other way d3-geo reads
      // this as the whole globe and fitExtent scales the planet into the frame.
      return {
        type: "Polygon",
        coordinates: [[[west, south], [west, north], [east, north], [east, south], [west, south]]]
      };
    }
    const exclude = new Set(chart.fitExclude ?? []);
    return {
      type: "FeatureCollection",
      features: geo.features.filter((f) => !exclude.has(f.properties.key))
    };
  });

  // How much room the widest label in this set needs, estimated from character
  // count because the layout has to be known before the text is laid out. Read
  // from the step's values rather than from `annotations`, which needs this.
  const labelWidth = $derived.by(() => {
    let longest = 0;
    for (const key of activeStep.highlight ?? []) {
      const v = chart.values[key];
      if (!v) continue;
      longest = Math.max(
        longest,
        v.label.length,
        `${v.per1k.toFixed(1)} per 1,000`.length,
        `${formatNet(v.net)} people`.length
      );
    }
    return Math.min(190, longest * CHAR_W + 10);
  });

  // The extent depends only on the width, the gutter and the plot height, never on
  // how many areas the step annotates. That is deliberate: it keeps the map exactly
  // the same size on the overview step and on the annotated one, so scrolling
  // between them moves labels rather than resizing the country. LEGEND_H is
  // reserved here too, unconditionally, so the map's scale never shifts between a
  // step that shows the legend and one that hides it for annotations.
  const projection = $derived.by(() => {
    const extent = [
      [gutter + PAD, PAD],
      [width - gutter - PAD, plotHeight - PAD - LEGEND_H]
    ];
    const p = d3.geoMercator().fitExtent(extent, fitTarget);

    // fitExtent centres what it fits. That is right when labels fall on both
    // sides, but a map whose areas all sit in one half sends every label the same
    // way, and the centred map then leaves a big hole on the other side. `align`
    // is set per chart rather than inferred from the annotations, so it cannot
    // change between a chart's overview step and its annotated one.
    if ((chart.align ?? "center") === "left") {
      const bounds = d3.geoPath(p).bounds(fitTarget);
      const shift = extent[0][0] - bounds[0][0];
      const [tx, ty] = p.translate();
      p.translate([tx + shift, ty]);
    }
    return p;
  });

  const path = $derived(d3.geoPath(projection));

  // Where the map actually ended up. A tall, narrow country fitted into a wide box
  // is height-constrained, so it leaves a lot of empty space either side. Anchoring
  // labels to the drawn edge rather than to the reserved gutter keeps the leader
  // lines short instead of running them across that emptiness.
  const mapBounds = $derived(path.bounds(fitTarget));

  // ── Annotations ──────────────────────────────────────────────────────────────

  /** Centroid of a feature's largest polygon, so a leader points at land rather
   *  than at the sea between two islands. */
  function landCentroid(feature) {
    const geometry = feature.geometry;
    if (geometry.type !== "MultiPolygon") return path.centroid(feature);

    let best = null;
    let bestArea = -Infinity;
    for (const rings of geometry.coordinates) {
      const part = {type: "Polygon", coordinates: rings};
      const area = Math.abs(path.area({type: "Feature", geometry: part}));
      if (area > bestArea) {
        bestArea = area;
        best = part;
      }
    }
    return path.centroid({type: "Feature", geometry: best});
  }

  /** Push overlapping labels apart in place: down first, then back up if the
   *  column has run past the bottom, so a crowded side stays inside the frame. */
  function dodge(items, slot, top, bottom) {
    items.sort((a, b) => a.y - b.y);
    for (let i = 1; i < items.length; i += 1) {
      items[i].y = Math.max(items[i].y, items[i - 1].y + slot);
    }
    if (items.length && items.at(-1).y > bottom) {
      items.at(-1).y = bottom;
      for (let i = items.length - 2; i >= 0; i -= 1) {
        items[i].y = Math.min(items[i].y, items[i + 1].y - slot);
      }
    }
    for (let i = 0; i < items.length; i += 1) {
      items[i].y = Math.max(items[i].y, top + i * slot);
    }
    return items;
  }

  /** Each annotation, fully positioned: where its text sits, how it is anchored,
   *  and the leader path back to its area. The two layouts differ only here. */
  const annotations = $derived.by(() => {
    const keys = activeStep.highlight ?? [];
    if (keys.length === 0) return [];

    const items = [];
    for (const key of keys) {
      const feature = geo.features.find((f) => f.properties.key === key);
      const value = chart.values[key];
      if (!feature || !value) continue;
      const [cx, cy] = landCentroid(feature);
      if (!Number.isFinite(cx) || !Number.isFinite(cy)) continue;
      items.push({key, cx, cy, ...value});
    }

    // A stack down each side, split by which half of the *map* the area sits in,
    // then pushed apart so no two labels collide. Splitting on the container's
    // midpoint instead sends every label the same way as soon as the map is not
    // centred in it.
    const middle = (mapBounds[0][0] + mapBounds[1][0]) / 2;
    for (const item of items) {
      item.side = item.cx < middle ? "left" : "right";
      item.dist = Math.abs(item.cx - middle);
      item.y = item.cy;
    }

    // Geography alone can strand every label on one side: a cluster of areas that
    // all sit south-west of centre sends the whole column left and leaves the
    // right column empty. Rebalance by count, moving whichever items sit closest
    // to the midline (the ones with the weakest geographic reason to be on their
    // side) to the emptier column until the two differ by at most one.
    let left = items.filter((i) => i.side === "left");
    let right = items.filter((i) => i.side === "right");
    while (Math.abs(left.length - right.length) > 1) {
      const [from, to, flip] =
        left.length > right.length ? [left, right, "right"] : [right, left, "left"];
      from.sort((a, b) => a.dist - b.dist);
      const moved = from.shift();
      moved.side = flip;
      to.push(moved);
    }

    const top = PAD + LABEL_SLOT / 2;
    const bottom = plotHeight - PAD - LABEL_SLOT / 2;
    for (const side of ["left", "right"]) {
      dodge(items.filter((i) => i.side === side), LABEL_SLOT, top, bottom);
    }

    for (const item of items) {
      // Just outside the drawn map, pulled in far enough that the text still fits.
      const x = item.side === "left"
        ? Math.max(labelWidth + PAD, mapBounds[0][0] - 26)
        : Math.min(width - labelWidth - PAD, mapBounds[1][0] + 26);
      const elbow = x + (item.side === "left" ? 14 : -14);
      item.tx = x;
      item.ty = item.y - LINE_H * 0.5;
      item.anchor = item.side === "left" ? "end" : "start";
      item.leader = `${item.cx},${item.cy} ${elbow},${item.y} ${x},${item.y}`;
    }
    return items;
  });

  // ── Fills ────────────────────────────────────────────────────────────────────

  const highlighted = $derived(new Set(activeStep.highlight ?? []));
  const isDim = (key) => highlighted.size > 0 && !highlighted.has(key);
  const fillFor = (key) => {
    const value = chart.values[key];
    return value ? color(value.per1k) : NO_DATA;
  };

  // ── Legend ───────────────────────────────────────────────────────────────────
  // The colour scale is piecewise, so the gradient stops have to sit at the same
  // proportional offsets as the domain breaks rather than being evenly spaced.

  const legend = $derived.by(() => {
    const domain = chart.scale.domain;
    const lo = domain[0];
    const hi = domain.at(-1);
    const span = hi - lo || 1;
    return {
      lo,
      hi,
      zero: lo < 0 ? ((0 - lo) / span) * 100 : null,
      stops: domain.map((d, i) => ({
        offset: ((d - lo) / span) * 100,
        color: chart.scale.range[i]
      }))
    };
  });

  const formatNet = (n) => (n >= 0 ? "+" : "") + d3.format(",.0f")(n);
  const gradientId = $derived(`legend-${chartId}`);
  const showLegend = $derived(width >= 720 || annotations.length === 0);
  const clipId = $derived(`clip-${chartId}`);

  // A framed map is clipped to its window, so areas that run past it (Rodney's
  // northern half here) end at a deliberate edge rather than at the SVG's.
  const clipRect = $derived.by(() => {
    if (!chart.fitBBox) return null;
    const [[x0, y0], [x1, y1]] = mapBounds;
    return {x: x0, y: y0, width: x1 - x0, height: y1 - y0};
  });
</script>

<div class="map" bind:clientWidth={width} bind:clientHeight={height}>
  <div class="map-header" style:padding-left="{rail}px">
    {#key chartId}
      <h2 class="map-title">{chart.title}</h2>
      <p class="map-subtitle">{chart.subtitle}</p>
    {/key}
  </div>

  <svg {width} height={plotHeight} role="img" aria-label={chart.title}>
    {#key chartId}
      <g class="layer">
        {#if clipRect}
          <defs>
            <clipPath id={clipId}>
              <rect {...clipRect} />
            </clipPath>
          </defs>
        {/if}

        <!-- Only the geography is clipped. Leader lines and labels sit outside the
             frame by design, so they must stay out of the clip. -->
        <g clip-path={clipRect ? `url(#${clipId})` : null}>
          {#each geo.features as feature (feature.properties.key)}
            {@const key = feature.properties.key}
            <path
              class="region"
              class:dim={isDim(key)}
              d={path(feature)}
              fill={fillFor(key)}
            />
          {/each}

          <!-- highlighted outlines, over every fill so no neighbour covers them -->
          {#each geo.features as feature (feature.properties.key)}
            {#if highlighted.has(feature.properties.key)}
              <path class="region-outline" d={path(feature)} />
            {/if}
          {/each}
        </g>

        <!-- leader lines and labels, positioned in placeInColumns/placeInBands -->
        {#each annotations as a (a.key)}
          <g class="annotation">
            <polyline class="leader" points={a.leader} />
            <circle class="leader-dot" cx={a.cx} cy={a.cy} r="3" />
            <text class="annotation-text" x={a.tx} y={a.ty} text-anchor={a.anchor}>
              <tspan class="annotation-name" x={a.tx}>{a.label}</tspan>
              <tspan class="annotation-value" x={a.tx} dy={LINE_H}>{a.per1k.toFixed(1)} per 1,000</tspan>
              <tspan class="annotation-value" x={a.tx} dy={LINE_H}>{formatNet(a.net)} people</tspan>
            </text>
          </g>
        {/each}

        <!-- Legend, centred under the map so it stays clear of the label columns.
             Sits in the LEGEND_H band the projection leaves free below the map, so
             it never overlaps the geography. A phone has no room for both legend
             and labels, and an annotated step already states the exact figures, so
             there the legend gives way to the labels. -->
        {#if showLegend}
        <g
          class="legend"
          transform="translate({(mapBounds[0][0] + mapBounds[1][0]) / 2 - 75},{plotHeight - LEGEND_H + 18})"
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" x2="100%">
              {#each legend.stops as stop}
                <stop offset="{stop.offset}%" stop-color={stop.color} />
              {/each}
            </linearGradient>
          </defs>
          <!-- backing, so the legend stays readable where the map runs behind it -->
          <rect class="legend-backing" x="-10" y="-18" width="170" height="46" rx="3" />
          <rect width="150" height="8" rx="1" fill="url(#{gradientId})" />
          <text class="legend-tick" x="0" y="20">{legend.lo.toFixed(0)}</text>
          <text class="legend-tick" x="150" y="20" text-anchor="end">{legend.hi.toFixed(0)}</text>
          {#if legend.zero !== null}
            <line class="legend-zero" x1={legend.zero * 1.5} x2={legend.zero * 1.5} y1="-2" y2="10" />
          {/if}
          <text class="legend-title" x="0" y="-6">Net per 1,000 residents</text>
        </g>
        {/if}
      </g>
    {/key}
  </svg>
</div>

<style>
  .map {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
  }

  .map-header {
    height: 62px;
    flex: none;
  }

  .map-title {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .map-subtitle {
    font-size: 0.8rem;
    color: var(--muted);
    margin: 0.15rem 0 0;
  }

  .map-header :global(h2),
  .map-header :global(p),
  .layer {
    animation: fade-in 0.45s ease both;
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  svg {
    overflow: hidden;
  }

  .region {
    stroke: var(--bg);
    stroke-width: 0.5;
    fill-opacity: 1;
    transition: fill-opacity 0.4s ease;
  }

  .region.dim {
    fill-opacity: 0.28;
  }

  .region-outline {
    fill: none;
    stroke: var(--fg);
    stroke-width: 1.4;
  }

  .leader {
    fill: none;
    stroke: var(--fg);
    stroke-width: 1;
    opacity: 0.55;
  }

  .leader-dot {
    fill: var(--fg);
  }

  /* One size at every width. LINE_H and CHAR_W in the script are set from these,
     so a change here needs a matching change there. */
  .annotation-name {
    font-size: 0.76rem;
    font-weight: 700;
    fill: var(--fg);
  }

  .annotation-value {
    font-size: 0.7rem;
    fill: var(--muted);
  }

  .legend-backing {
    fill: var(--bg);
    opacity: 0.82;
  }

  .legend-tick {
    font-size: 0.68rem;
    fill: var(--tick);
  }

  .legend-title {
    font-size: 0.68rem;
    fill: var(--faint);
  }

  .legend-zero {
    stroke: var(--fg);
    stroke-width: 1;
    opacity: 0.6;
  }
</style>
