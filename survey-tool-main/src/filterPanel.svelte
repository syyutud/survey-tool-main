<script>
  import FilterGroup from "./components/filterGroup.svelte";
  import { Accordion, Badge, Heading } from 'flowbite-svelte';

  import Timeline from "./components/timeline.svelte";
  import { filterBy } from "./store"

  export let freq = {};
  export let selectTopics = [];
  export const filteredFreq = {};
  
	export let data;
	export let filteredData;

 $: topics = Array.isArray(selectTopics) ? selectTopics : [];

  const removeSelection = (select) => {
    $filterBy.forEach((prop) => {
      if (prop.values) {
          prop.selected = prop.selected.filter((topic) => topic !== select);
      } else {
        prop.categories.forEach((option) => {
            option.selected = option.selected.filter(
              (topic) => topic !== select
            );
        });
      }
    });
    $filterBy = $filterBy;
  };

  let secondary = true

  const onChange = () => {
    console.log(secondary)
    $filterBy.forEach((prop) => {
      if (secondary && prop.values) {
        prop.valuesTemp = structuredClone(prop.values);
        prop.values = prop.values.filter((c) => c.contains("(-)"));
      } else if (!secondary && prop.values) {
        prop.values = prop.valuesTemp.filter((c) => c);
      }
    });
    $filterBy = $filterBy;
  };

</script>

<div class="accordion-container">
  
  <div>
		{#each topics as topic }
			<Badge class="p-2 h-5 ml-1" large on:close={(e) => removeSelection(topic)}>{topic}</Badge>
		{/each}
  </div>

  
  <Timeline {filteredData} {data} />
  
  <Accordion multiple>
  {#each $filterBy as prop}

    <!-- Flat filter item -->
    {#if prop && prop.name && Array.isArray(prop.values)}
      <FilterGroup
        name={prop.name}
        values={prop.values ?? []}
        selected={prop.selected ?? []}
        freqGroup={freq?.[prop.name] ?? {}}
        on:message
      />

    <!-- Grouped filter item -->
    {:else if prop && prop.groupName && Array.isArray(prop.categories)}
      <Heading tag="h6" class="mt-5">{prop.groupName}</Heading>

      {#each prop.categories as cate}
        {#if cate && cate.name}
          <FilterGroup
            name={cate.name}
            values={cate.values ?? []}
            selected={cate.selected ?? []}
            freqGroup={freq?.[cate.name] ?? {}}
            on:message
          />
        {/if}
      {/each}

    {/if}

  {/each}
</Accordion>

</div>
