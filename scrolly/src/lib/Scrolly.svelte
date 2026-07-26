<script>
  import {onMount} from "svelte";
  import scrollama from "scrollama";

  // The reusable scroll engine. It listens for step elements entering the
  // viewport and exposes the active index via a bindable prop. Nothing here is
  // specific to any chart or dataset - copy it between stories unchanged.
  let {steps, active = $bindable(0), graphic, narrative} = $props();

  let container;

  // Trigger just below the sticky chart, so a step goes active as it settles
  // under the graphic it describes rather than when it crosses the chart's
  // middle. The chart is shorter on a phone, so the trigger rises with it and
  // the step keeps the same clear band underneath either way. Both numbers
  // track .scrolly-graphic's height in the stylesheet below.
  const offsetFor = () => (innerWidth < 720 ? 0.62 : 0.78);

  onMount(() => {
    const scroller = scrollama();

    scroller
      .setup({step: ".scrolly-step", offset: offsetFor()})
      .onStepEnter(({index}) => {
        active = index;
      });

    const onResize = () => {
      scroller.offset(offsetFor());
      scroller.resize();
    };
    addEventListener("resize", onResize);

    return () => {
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
        {@render narrative(step, i)}
      </div>
    {/each}
  </div>
</div>

<style>
  /* The chart pins to the top of the viewport and keeps the top 62vh to itself.
     Narrative scrolls through the clear band underneath it and passes behind the
     chart on the way out, so text never covers the graphic it describes. */
  .scrolly {
    max-width: 56rem;
    margin: 0 auto;
    padding: 0 1.5rem;
    position: relative;
  }

  .scrolly-graphic {
    position: sticky;
    top: 0;
    height: 62vh;
    padding-top: 1.25rem;
    display: flex;
    align-items: center;
    /* Opaque and above the narrative: steps slide behind the chart rather than
       over it. */
    z-index: 2;
    background: var(--bg);
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

  .scrolly-step {
    margin: 0 0 62vh;
    max-width: 34rem;
    min-height: 26vh;
    padding: 1.25rem 0 0;
    opacity: 0.22;
    transition: opacity 0.35s ease;
  }

  /* The last step keeps enough room to go active before the chart releases,
     then the page hands over to the sources block. */
  .scrolly-step:last-child {
    margin-bottom: 24vh;
  }

  .scrolly-step.is-active {
    opacity: 1;
  }

  @media (max-width: 720px) {
    .scrolly-graphic {
      height: 46vh;
    }

    .scrolly-narrative {
      padding-left: 42px;  /* MARGIN_NARROW.left in Chart.svelte */
    }

    .scrolly-step {
      margin-bottom: 55vh;
    }
  }
</style>
