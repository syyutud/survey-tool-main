<script>
  import { Tooltip, Button, P } from "flowbite-svelte";
  import { AccordionItem, Accordion } from "flowbite-svelte";
  import { CogOutline } from "flowbite-svelte-icons";

  import StackGraph from "./vis/stackGraph.svelte";
  import CorrMetric from "./vis/corrMetric.svelte";
  import GraphView from "./vis/GraphView.svelte";

  import { filterBy } from "./store";

  export let data = [];

  // 生成维度列表（防止重复 push + 防 undefined）
  $: choicesDim = ($filterBy ?? []).map((prop, i) =>
    prop && "groupName" in prop
      ? { name: prop.groupName, index: i }
      : { name: prop?.name, index: i }
  ).filter(d => !!d.name);

  // 默认选择（必须防 choicesDim 不足）
  $: selectedDimX = choicesDim.length > 0 ? choicesDim[0] : null;
  $: selectedDimY = choicesDim.length > 1 ? choicesDim[1] : selectedDimX;

  $: selectedCate = choicesDim.length > 0 ? choicesDim[0] : null;
  $: selectedSubCate = "All";
  $: subCates = [];

  $: if (selectedCate && ($filterBy?.[selectedCate.index]) && ("groupName" in $filterBy[selectedCate.index])) {
    subCates = ["All", ...($filterBy[selectedCate.index].categories ?? []).map(c => c.name)];
  } else {
    subCates = [];
    selectedSubCate = selectedCate?.name ?? "All";
  }

  function showHideSettings(which) {
    Array.from(document.getElementsByClassName(which)).forEach((el) => {
      el.classList.toggle("hidden");
    });
  }
</script>

<div class="vis-panel dark:bg-gray-900">
  <Accordion>

    <!-- 1) Graph View（放最上） -->
    <AccordionItem open={true}>
      <div slot="header" style="display:flex">
        Graph View
        <Button
          pill
          outline
          class="!p-1 border-0"
          id="graph-settings"
          on:click={(e) => {
            e.stopPropagation();
            showHideSettings("graph-hidable");
          }}
        >
          <CogOutline />
          <Tooltip triggeredBy="#graph-settings" placement="bottom">Settings</Tooltip>
        </Button>
      </div>

      <div class="graph-hidable hidden">
        <P style="padding-left:20px">Graph settings placeholder</P>
      </div>

      <GraphView {data} />
    </AccordionItem>

    <!-- 2) Correlation Matrix -->
    <AccordionItem open={true}>
      <div slot="header" style="display:flex">
        Correlation Matrix
        <Button
          pill
          outline
          class="!p-1 border-0"
          id="corr-settings"
          on:click={(e) => {
            e.stopPropagation();
            showHideSettings("corr-hidable");
          }}
        >
          <CogOutline />
          <Tooltip triggeredBy="#corr-settings" placement="bottom">Settings</Tooltip>
        </Button>
      </div>

      {#if choicesDim.length >= 1}
        <div class="flexy">
          <div class="flex flex-wrap space-x-1 pb-3 items-center corr-hidable hidden">
            <P style="padding-left:20px">X-Axis:</P>
            {#each choicesDim as dim}
              <Button
                size="sm"
                outline
                class="p-1 {dim.name === selectedDimX?.name
                  ? 'dark:bg-gray-400 dark:text-primary-200'
                  : 'cursor-pointer'}"
                on:click={() => (selectedDimX = dim)}
              >
                {dim.name}
              </Button>
            {/each}
          </div>

          <div class="flex flex-wrap space-x-1 items-center corr-hidable hidden">
            <P style="padding-left:20px">Y-Axis:</P>
            {#each choicesDim as dim}
              <Button
                outline
                size="sm"
                class="p-1 {dim.name === selectedDimY?.name
                  ? 'dark:bg-gray-400 dark:text-primary-200'
                  : 'cursor-pointer'}"
                on:click={() => (selectedDimY = dim)}
              >
                {dim.name}
              </Button>
            {/each}
          </div>
        </div>

        <CorrMetric
          {data}
          selectedDimX={selectedDimX?.name}
          selectedDimY={selectedDimY?.name}
          on:message
        />
      {:else}
        <P style="padding-left:20px">No dimensions available (check survey-config.json filterBy).</P>
      {/if}
    </AccordionItem>

    <!-- 3) Over the Years -->
    <AccordionItem>
      <div slot="header" style="display:flex">
        Over the Years
        <Button
          pill
          outline
          class="!p-1 border-0"
          id="stack-settings"
          on:click={(e) => {
            e.stopPropagation();
            showHideSettings("stack-hidable");
          }}
        >
          <CogOutline />
          <Tooltip triggeredBy="#stack-settings" placement="bottom">Settings</Tooltip>
        </Button>
      </div>

      {#if choicesDim.length >= 1}
        <div class="flexy">
          <div class="stack-hidable hidden">
            <div class="flex flex-wrap space-x-1 pb-3 items-center">
              <P style="padding-left:20px">Categories:</P>
              {#each choicesDim as dim}
                <Button
                  size="sm"
                  outline
                  class="p-1 {dim.name === selectedCate?.name
                    ? 'dark:bg-gray-400 dark:text-primary-200'
                    : 'cursor-pointer'}"
                  on:click={() => (selectedCate = dim)}
                >
                  {dim.name}
                </Button>
              {/each}
            </div>

            {#if subCates.length > 0}
              <div class="flex flex-wrap space-x-1 pb-3 items-center">
                <P style="padding-left:20px">Sub-Categories:</P>
                {#each subCates as subcate}
                  <Button
                    size="sm"
                    outline
                    class="p-1 {subcate === selectedSubCate
                      ? 'dark:bg-gray-400 dark:text-primary-200'
                      : 'cursor-pointer'}"
                    on:click={() => (selectedSubCate = subcate)}
                  >
                    {subcate}
                  </Button>
                {/each}
              </div>
            {/if}
          </div>

          <StackGraph
            {data}
            selectedCate={selectedSubCate === "All" ? selectedCate?.name : selectedSubCate}
            on:message
          />
        </div>
      {:else}
        <P style="padding-left:20px">No dimensions available (check survey-config.json filterBy).</P>
      {/if}
    </AccordionItem>

  </Accordion>
</div>

<style>
  .vis-panel {
    padding: 10px 5px;
    height: 100%;
    width: 100%;
  }
  .hidden {
    display: none;
  }
</style>
