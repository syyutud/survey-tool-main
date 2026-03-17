<script>
  import { Button, P } from "flowbite-svelte";
  import CorrMetric from "./corrMetric.svelte";
  import StackGraph from "./stackGraph.svelte";
  import TrendencyAnalysis from "./trendencyAnalysis.svelte";
  import { filterBy, detailTool } from "../store";

  export let data = [];
  export let allData = [];  
  export let meta = {};
  export let structure;

  $: choicesDim = ($filterBy ?? []).flatMap((g) => {
    if (g && "groupName" in g && Array.isArray(g.categories)) {
      return g.categories
        .filter((c) => !!c?.name)
        .map((c) => ({
          key: c.name,
          label: c.label ?? c.name
        }));
    }

    if (g?.name) {
      return [{ key: g.name, label: g.label ?? g.name }];
    }
    return [];
  });

  $: selectedDimX = choicesDim.length > 0 ? choicesDim[0] : null;
  $: selectedDimY = choicesDim.length > 1 ? choicesDim[1] : selectedDimX;
  $: selectedCate = choicesDim.length > 0 ? choicesDim[0] : null;
</script>

<div class="detail-root">
  {#if $detailTool === "correlation"}
    <div class="mb-3">
      <P class="mb-2">Correlation Matrix</P>
      <CorrMetric allData={allData} />
    </div>

  {:else if $detailTool === "overtheyear"}
    <div class="mb-3">
      <P class="mb-2">Over the Years</P>

      <div class="flex flex-wrap gap-2 mb-3 items-center">
        <P>Categories:</P>
        {#each choicesDim as dim}
          <Button size="xs" outline on:click={() => (selectedCate = dim)}>
            {dim.label}
          </Button>
        {/each}
      </div>

      <StackGraph {data} {meta} selectedCate={selectedCate?.key} />
    </div>

  {:else if $detailTool === "trend"}
    <TrendencyAnalysis {data} {meta} />

  {/if}
</div>

<style>
  .detail-root {
    padding: 16px;
    height: 100%;
    width: 100%;
    background: var(--app-bg);
    color: var(--text);
    overflow: auto;
    box-sizing: border-box;
  }
</style>