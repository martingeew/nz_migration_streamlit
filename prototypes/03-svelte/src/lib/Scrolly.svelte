<script>
  import {onMount} from "svelte";
  import scrollama from "scrollama";

  let {steps, active = $bindable(0), graphic, narrative} = $props();

  let container;

  onMount(() => {
    const scroller = scrollama();

    scroller
      .setup({step: ".scrolly-step", offset: 0.6})
      .onStepEnter(({index}) => {
        active = index;
      });

    const onResize = () => scroller.resize();
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
  .scrolly {
    display: grid;
    grid-template-columns: 1fr 22rem;
    gap: 3rem;
    max-width: 68rem;
    margin: 0 auto;
    padding: 0 1.5rem;
    align-items: start;
  }

  .scrolly-graphic {
    position: sticky;
    top: 0;
    height: 100vh;
    display: flex;
    align-items: center;
    /* Grid tracks default to min-width:auto, so the SVG would otherwise widen
       the column past the container and force a horizontal scrollbar. */
    min-width: 0;
  }

  .scrolly-narrative {
    padding: 40vh 0;
  }

  .scrolly-step {
    margin-bottom: 80vh;
    padding: 1.5rem;
    border-radius: 0.5rem;
    background: #f6f8f8;
    opacity: 0.35;
    transition: opacity 0.35s ease;
  }

  .scrolly-step.is-active {
    opacity: 1;
  }

  @media (max-width: 720px) {
    .scrolly {
      grid-template-columns: 1fr;
      gap: 0;
    }

    .scrolly-graphic {
      height: 55vh;
      background: white;
      z-index: 2;
    }

    .scrolly-narrative {
      padding: 0;
    }

    .scrolly-step {
      margin-bottom: 60vh;
    }
  }
</style>
