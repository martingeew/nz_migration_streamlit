<script>
  // Theme: swap this one import to change the whole look. Every colour, grid
  // line, and tick reads from the CSS variables it defines.
  //   ./styles/minimalist-white.css
  //   ./styles/minimalist-dark.css  (used here)
  import "./styles/minimalist-dark.css";

  import data from "./data/story.json";
  import Chart from "./lib/Chart.svelte";
  import Scrolly from "./lib/Scrolly.svelte";

  let step = $state(0);
</script>

<header class="hero">
  <p class="byline">{data.meta.byline}</p>
  <h1>{data.meta.title}</h1>
  <p class="standfirst">{data.meta.standfirst}</p>
  <p class="kicker">Scroll to advance.</p>
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
  <p class="data-note">
    Data to {data.meta.end}, generated {data.meta.generated}. {data.meta.byline}.
  </p>
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

  .hero h1 {
    font-size: clamp(2rem, 5vw, 3rem);
    line-height: 1.1;
    margin-bottom: 1rem;
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
