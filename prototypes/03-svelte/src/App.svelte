<script>
  import data from "../../data/net_migration_citizenship.json";
  import Chart from "./lib/Chart.svelte";
  import Scrolly from "./lib/Scrolly.svelte";

  let step = $state(0);

  const peak = data.annotations.peak;
</script>

<header class="hero">
  <h1>Two migration stories in one line</h1>
  <p class="standfirst">
    New Zealand's net migration hit a record {peak.value.toLocaleString()} in the
    year to {peak.label}. The headline number hid two opposite movements
    underneath it.
  </p>
  <p class="kicker">
    Prototype C of 3 — Vite + Svelte + Scrollama + D3. Scroll to advance.
  </p>
</header>

<Scrolly steps={data.steps} bind:active={step}>
  {#snippet graphic()}
    <Chart {step} />
  {/snippet}

  {#snippet narrative(s)}
    <h2>{s.title}</h2>
    <p>{s.body}</p>
  {/snippet}
</Scrolly>

<footer class="outro">
  <h2>What this prototype shows</h2>
  <p>
    All three series stay in the DOM the whole time. Steps fade them in and out,
    and the y-axis domain is interpolated with
    <code>d3.interpolateArray</code> inside a <code>requestAnimationFrame</code>
    loop, so the lines genuinely morph between steps instead of snapping.
  </p>
  <p>
    That control is the tradeoff. Nothing here came for free: the axes, grid,
    ticks, labels, and annotation are all hand-drawn SVG, which is roughly 200
    lines that Plotly and Observable Plot would have given you in ten.
  </p>
  <p class="data-source">
    Source: Statistics NZ ITM552301 — migrant arrivals and departures by
    citizenship. 12-month rolling sum.
  </p>
</footer>

<style>
  .hero {
    max-width: 42rem;
    margin: 4rem auto 6rem;
    padding: 0 1.5rem;
  }

  .hero h1 {
    font-size: clamp(2rem, 5vw, 3rem);
    line-height: 1.1;
    margin-bottom: 1rem;
  }

  .standfirst {
    font-size: 1.15rem;
    line-height: 1.55;
    color: #555;
  }

  .kicker {
    font-size: 0.85rem;
    color: #999;
    margin-top: 1.5rem;
  }

  .outro {
    max-width: 42rem;
    margin: 6rem auto 4rem;
    padding: 0 1.5rem;
    color: #333;
  }

  .data-source {
    font-size: 0.8rem;
    color: #95a5a6;
    margin-top: 2rem;
  }
</style>
