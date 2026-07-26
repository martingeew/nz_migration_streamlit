<script>
  import {onMount} from "svelte";
  import scrollama from "scrollama";

  // The reusable scroll engine. It listens for step elements entering the
  // viewport and exposes the active index via a bindable prop. Nothing here is
  // specific to any chart or dataset - copy it between stories unchanged.
  let {steps, active = $bindable(0), graphic, narrative} = $props();

  let container;

  // Each step's text sticks just under the chart for the length of its scroll
  // zone (see .scrolly-step-exit below), so every step is read in the same
  // place, directly beneath the graphic it describes. A step goes active exactly
  // as its text arrives there. Both numbers are read back from the rendered
  // stylesheet rather than repeated here, so a breakpoint cannot put the trigger
  // and the text in different places.
  function chartHeight() {
    const graphic = container?.querySelector(".scrolly-graphic");
    return graphic ? graphic.getBoundingClientRect().height : innerHeight * 0.62;
  }

  function stickGap() {
    if (!container) return 28;
    const value = parseFloat(getComputedStyle(container).getPropertyValue("--stick-gap"));
    return Number.isFinite(value) ? value : 28;
  }

  const offsetFor = () =>
    Math.min(0.9, (chartHeight() + stickGap()) / innerHeight);

  // A step stays "active" from the moment it triggers until the next one does,
  // which means it keeps rising long after it has passed the chart's lower edge.
  // Scroll position, not active state, decides how much of it is left: it
  // dissolves as it travels up over the chart instead of being cut off by the
  // graphic's edge. Applied to an inner element so it multiplies with the
  // active/inactive opacity in the stylesheet rather than fighting its
  // transition.
  // Must stay below --stick-gap, or the text would sit slightly faded for the
  // whole time it is parked under the chart.
  const FADE_LEAD_PX = 12;     // starts fading this far below the chart's edge
  // Roughly half the chart's height, so the outgoing step stays legible well up
  // the plot instead of winking out just above the axis labels. Keep the product
  // under --exit-travel, or the zone runs out with opacity still to spend.
  const FADE_FRACTION = 0.55;
  const FADE_MIN_PX = 220;

  function paintExit() {
    const graphic = container?.querySelector(".scrolly-graphic");
    if (!graphic) return;

    const box = graphic.getBoundingClientRect();

    // Only once the chart has actually pinned. Before that it is still scrolling
    // into place with the first step flush beneath it in document flow, which
    // would otherwise sit inside the fade zone and never reach full strength.
    const pinned = box.top <= 1;

    // Fading begins just below the chart, so the step is already softening by
    // the time it reaches the axis labels rather than landing on them at full
    // strength, and it has gone by the time it would reach the plot.
    const edge = box.bottom + FADE_LEAD_PX;
    const distance = Math.max(FADE_MIN_PX, edge * FADE_FRACTION);

    for (const el of container.querySelectorAll(".scrolly-step")) {
      const inner = el.firstElementChild;
      if (!inner) continue;
      // The inner element is the sticky one, so measure it rather than its
      // scroll zone: while it is parked under the chart this stays negative and
      // the text holds full strength, and it only climbs once the zone releases.
      const risen = pinned ? edge - inner.getBoundingClientRect().top : 0;
      inner.style.opacity = risen <= 0 ? "1" : String(Math.max(0, 1 - risen / distance));
    }
  }

  onMount(() => {
    const scroller = scrollama();

    scroller
      .setup({step: ".scrolly-step", offset: offsetFor()})
      .onStepEnter(({index}) => {
        active = index;
      });

    let frame = null;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = null;
        paintExit();
      });
    };

    const onResize = () => {
      scroller.offset(offsetFor());
      scroller.resize();
      paintExit();
    };

    paintExit();
    addEventListener("scroll", onScroll, {passive: true});
    addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(frame);
      removeEventListener("scroll", onScroll);
      removeEventListener("resize", onResize);
      scroller.destroy();
    };
  });
</script>

<div class="scrolly" bind:this={container}>
  <div class="scrolly-graphic">
    {@render graphic()}
  </div>

  <div class="scrolly-narrative">
    {#each steps as step, i}
      <div class="scrolly-step" class:is-active={i === active}>
        <!-- paintExit() sets this element's opacity; the outer one carries the
             active/inactive state. Nesting multiplies the two. -->
        <div class="scrolly-step-exit">
          {@render narrative(step, i)}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  /* The chart pins to the top of the viewport and keeps --chart-h to itself.
     Each step's text then parks just beneath it for the length of that step's
     scroll zone, so every step is read in the same place, directly under the
     graphic. When the zone runs out the text climbs over the chart and dissolves
     (see paintExit above), rather than being clipped behind an opaque edge.

     --chart-h is the single source of truth: the graphic's height, the sticky
     offset for the text and the scrollama trigger all derive from it. */
  .scrolly {
    --chart-h: 62vh;
    --stick-gap: 28px;  /* read back by stickGap() above; must exceed FADE_LEAD_PX */
    /* How far a step climbs over the chart while dissolving, and so also the gap
       that opens up before the next step's text arrives: one zone's bottom is the
       next one's top, so without this room the two would sit flush against each
       other. Keep it comfortably above paintExit's fade distance, or the text
       still has opacity left when its zone runs out. */
    --exit-travel: 42vh;
    /* Scroll distance a step's text stays parked under the chart, before the
       climb starts. The zone is the two added together. */
    --step-read: 80vh;
    max-width: 56rem;
    margin: 0 auto;
    padding: 0 1.5rem;
    position: relative;
  }

  .scrolly-graphic {
    position: sticky;
    top: 0;
    height: var(--chart-h);
    padding-top: 1.25rem;
    display: flex;
    align-items: center;
    /* Behind the narrative and with no background of its own, so a step leaving
       the screen travels over the chart and stays readable. */
    z-index: 0;
    /* Flex children default to min-width:auto, so the SVG would otherwise widen
       the column past the container and force a horizontal scrollbar. */
    min-width: 0;
  }

  .scrolly-narrative {
    position: relative;
    z-index: 1;
    /* Matches Chart.svelte's left margin, so step text lines up with the chart
       title and the y-axis rather than floating in the middle of the column. */
    padding-left: 52px;
  }

  /* Each step is a tall scroll zone rather than a block of text with a gap after
     it: reading room, then room for the text to climb away over the chart. */
  .scrolly-step {
    margin: 0;
    min-height: calc(var(--step-read) + var(--exit-travel));
    opacity: 0.22;
    transition: opacity 0.35s ease;
  }

  /* The last zone needs no climb-away room; nothing follows it. */
  .scrolly-step:last-child {
    min-height: var(--step-read);
  }

  .scrolly-step.is-active {
    opacity: 1;
  }

  /* The sticky element, parked just below the chart. The bottom margin is what
     releases it --exit-travel early, so it climbs over the chart while the next
     step's text is still that far below the fold. A sticky element is held inside
     its containing block by its margin box, which is what makes this work. */
  .scrolly-step-exit {
    position: sticky;
    top: calc(var(--chart-h) + var(--stick-gap));
    margin-bottom: var(--exit-travel);
    max-width: 34rem;
  }

  @media (max-width: 720px) {
    .scrolly {
      --chart-h: 46vh;
      --stick-gap: 20px;
      --exit-travel: 34vh;
      --step-read: 74vh;
    }

    .scrolly-narrative {
      padding-left: 42px;  /* MARGIN_NARROW.left in Chart.svelte */
    }
  }
</style>
