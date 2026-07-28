<script>
  // Theme: swap this one import to change the whole look. Every colour, grid
  // line, and tick reads from the CSS variables it defines.
  //   ./styles/minimalist-white.css
  //   ./styles/minimalist-dark.css  (used here)
  import "./styles/minimalist-dark.css";

  import data from "./data/story.json";
  import Chart from "./lib/Chart.svelte";
  import MapChart from "./lib/MapChart.svelte";
  import Scrolly from "./lib/Scrolly.svelte";

  let step = $state(0);

  // Two graphic components, each of which only understands its own kind of chart.
  // Rather than swap them, both stay mounted and cross-fade, and each is fed the
  // most recent step of its own kind. So the time-series chart holds its last
  // frame behind the maps instead of being handed a map definition it cannot draw.
  const kindOf = (i) => data.charts[data.steps[i].chart].kind ?? "series";

  function lastOfKind(upTo, kind) {
    for (let i = upTo; i >= 0; i -= 1) if (kindOf(i) === kind) return i;
    return null;
  }

  const showMap = $derived(kindOf(step) === "map");
  const seriesStep = $derived(lastOfKind(step, "series") ?? 0);
  const mapStep = $derived(lastOfKind(step, "map"));
</script>

<header class="hero">
  <p class="byline">
    <a href="https://autonomousecon.substack.com" target="_blank" rel="noopener">
      {data.meta.byline} 🔗
    </a>
  </p>
  <h1>{data.meta.title}</h1>
  <p class="last-update">Last update: {data.meta.generated_label}</p>
  <p class="standfirst">{data.meta.standfirst}</p>
  <p class="kicker">Scroll to advance.</p>
</header>

<Scrolly steps={data.steps} bind:active={step}>
  {#snippet graphic()}
    <div class="graphic-stack">
      <div class="graphic-layer" class:faded={showMap}>
        <Chart step={seriesStep} />
      </div>
      {#if mapStep !== null}
        <div class="graphic-layer" class:faded={!showMap}>
          <MapChart step={mapStep} />
        </div>
      {/if}
    </div>
  {/snippet}

  {#snippet narrative(s)}
    <h2>{s.title}</h2>
    <p>{s.body}</p>
  {/snippet}
</Scrolly>

<!-- Sources and notes sit past the last step, so they arrive once the story has
     ended rather than competing with the chart the whole way down. -->
<footer class="outro">
  <h2>Sources and notes</h2>
  {#each data.meta.sources as source}
    <p class="data-source">{source}</p>
  {/each}
  {#each data.meta.notes as note}
    <p class="data-note">{note}</p>
  {/each}
</footer>

<style>
  /* Hero and outro sit on the same left rail as the chart title and y-axis:
     the .scrolly column (56rem) plus Chart.svelte's left margin. */
  .hero,
  .outro {
    max-width: 56rem;
    margin: 0 auto;
    padding: 0 1.5rem 0 calc(1.5rem + 52px);
  }

  .hero {
    margin-top: 5rem;
    margin-bottom: 7rem;
  }

  .hero h1,
  .hero .standfirst {
    max-width: 34rem;
  }

  .byline {
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--faint);
    margin: 0 0 1rem;
  }

  .byline a {
    color: inherit;
    text-decoration: none;
  }

  .byline a:hover {
    text-decoration: underline;
  }

  .hero h1 {
    font-size: clamp(2rem, 5vw, 3rem);
    line-height: 1.1;
    margin-bottom: 0.5rem;
  }

  .last-update {
    font-size: 0.85rem;
    font-style: italic;
    color: var(--faint);
    margin: 0 0 1.25rem;
  }

  .standfirst {
    font-size: 1.15rem;
    line-height: 1.55;
    color: var(--muted);
  }

  .kicker {
    font-size: 0.85rem;
    color: var(--faint);
    margin-top: 1.5rem;
  }

  /* The two graphic layers occupy the same box so one can fade into the other. */
  .graphic-stack {
    position: relative;
    width: 100%;
    height: 100%;
    min-width: 0;
  }

  .graphic-layer {
    position: absolute;
    inset: 0;
    transition: opacity 0.5s ease;
  }

  .graphic-layer.faded {
    opacity: 0;
    pointer-events: none;
  }

  .outro {
    margin-bottom: 6rem;
    border-top: 1px solid var(--panel-border);
    padding-top: 1.5rem;
  }

  .outro h2 {
    font-size: 1rem;
    margin: 0 0 1rem;
  }

  .data-source,
  .data-note {
    font-size: 0.8rem;
    line-height: 1.5;
    color: var(--faint);
    margin: 0 0 0.5rem;
    max-width: 40rem;
  }

  @media (max-width: 720px) {
    .hero,
    .outro {
      padding-left: calc(1.5rem + 42px);  /* MARGIN_NARROW.left in Chart.svelte */
    }
  }

  :global(.scrolly-step h2) {
    font-size: 1.35rem;
    margin: 0 0 0.6rem;
  }

  :global(.scrolly-step p) {
    margin: 0;
    font-size: 1.05rem;
    line-height: 1.6;
    color: var(--muted);
  }

  /* A phone gives the text a much narrower column and less height beneath the
     chart, so the desktop sizes run to too many lines. */
  @media (max-width: 720px) {
    .hero h1 {
      margin-bottom: 0.75rem;
    }

    .standfirst {
      font-size: 1rem;
    }

    :global(.scrolly-step h2) {
      font-size: 1.1rem;
      margin-bottom: 0.45rem;
    }

    :global(.scrolly-step p) {
      font-size: 0.92rem;
      line-height: 1.55;
    }
  }
</style>
