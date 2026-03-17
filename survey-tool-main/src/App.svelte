<script>
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import { P, Button, Drawer, Heading } from "flowbite-svelte";
  import { CloseSolid, ReplyOutline } from "flowbite-svelte-icons";
  import Header from "./header.svelte";
  import FilterPanel from "./filterPanel.svelte";
  import PaperCard from "./components/paperCard.svelte";
  import SearchField from "./components/searchField.svelte";
  import GraphView from "./vis/GraphView.svelte";
  import DetailView from "./vis/DetailView.svelte";
  import structureRaw from "./data/survey-config.json";
  import dataMetaRaw from "./data/survey-data.json";
  import {
    themeMode,
    viewMode,
    searchFilter,
    timeFilters,
    filterBy,
    trendSelection
  } from "./store";
  import { sineIn } from "svelte/easing";
  import { onDestroy } from "svelte";
  const unsubTheme = themeMode.subscribe((m) => {
    document.body.classList.toggle("light", m === "light");
    document.body.classList.toggle("dark", m !== "light");
  });
  onDestroy(() => unsubTheme());
  let headerPx = 56;
  let breakPoint = 1024;
  const drawerWidth = 320;
  let innerWidth = 0;
  let innerHeight = 0;
  let drawerHidden = false;
  let activateClickOutside = true;
  let backdrop = false;
  let showVis = true;
  let showPapers = true;
  let transitionParams = { x: -drawerWidth, duration: 200, easing: sineIn };

  $: mainLeft = innerWidth >= breakPoint && !drawerHidden ? drawerWidth : 0;
  $: mainWidth = innerWidth - mainLeft;
  $: mainHeight = innerHeight - headerPx;
  let filteredData = [];
  let freq = {};
  let meta = {};
  let selectTopics = [];

  function normalizeStructure(s) {
  const safe = s ?? {};
  const topView =
    safe.topView ?? { title: "Survey", description: "", authors: "", addEntry: {} };

  let filterByArr = safe.filterBy ?? [];

  // Case A: filterBy is ["A","B"] (flat)
  if (Array.isArray(filterByArr) && filterByArr.length > 0 && typeof filterByArr[0] === "string") {
    filterByArr = filterByArr.map((name) => ({ name }));
  }
  if (Array.isArray(filterByArr)) {
    filterByArr = filterByArr.map((item) => {
      if (item && typeof item === "object" && item.groupName && Array.isArray(item.categories)) {
        const cats = item.categories.map((c) => (typeof c === "string" ? { name: c } : c));
        return { ...item, categories: cats };
      }
      return item;
    });
  }

  const detailView =
    Array.isArray(safe.detailView) ? { show: safe.detailView } : safe.detailView ?? { show: [] };

  return { ...safe, topView, filterBy: filterByArr, detailView };
}

  

  function normalizeData(d) {
    const safe = d ?? {};
    return {
      meta: Array.isArray(safe.meta) ? safe.meta : [],
      data: Array.isArray(safe.data) ? safe.data : []
    };
  }

  const structure = normalizeStructure(structureRaw);
  const dataMeta = normalizeData(dataMetaRaw);

  meta = {};
  (dataMeta.meta ?? []).forEach((m) => {
    if (m?.name) meta[m.name] = m;
  });

  $filterBy = structuredClone(structure.filterBy ?? []);
  $: if (dataMeta?.data?.length && $filterBy?.length) {
  addMissingValues();
  }
  function addMissingValues() {
  $filterBy.forEach((group) => {

    // Grouped format: { groupName, categories: [...] }
    if (group && "groupName" in group && Array.isArray(group.categories)) {
      group.categories.forEach((cate) => {
        if (!cate?.name) return;

        const topics = new Set();
        dataMeta.data.forEach((paper) => {
          const v = paper?.[cate.name];         
          if (Array.isArray(v)) v.forEach((w) => w && topics.add(w));
          else if (typeof v === "string" && v.trim()) topics.add(v.trim());
        });

        cate.values = [...topics].sort((a, b) => a.localeCompare(b)); 
        cate.selected = Array.isArray(cate.selected) ? cate.selected : [];
      });

    } else if (group?.name) {
      const topics = new Set();
      dataMeta.data.forEach((paper) => {
        const v = paper?.[group.name];
        if (Array.isArray(v)) v.forEach((w) => w && topics.add(w));
        else if (typeof v === "string" && v.trim()) topics.add(v.trim());
      });

      group.values = [...topics].sort((a, b) => a.localeCompare(b));
      group.selected = Array.isArray(group.selected) ? group.selected : [];

    } else {
      group.selected = Array.isArray(group?.selected) ? group.selected : [];
    }
  });

  $filterBy = $filterBy;
}

  function freqCount(prop, arrValue, freqDict) {
    if (prop in meta && meta[prop]?.type === "MultiSelect") {
      if (!Array.isArray(arrValue)) return;
      if (arrValue.length === 1 && arrValue[0] === "") return;
      arrValue.forEach((value) => {
        if (!value) return;
        if (prop in freqDict) {
          freqDict[prop][value] ? freqDict[prop][value]++ : (freqDict[prop][value] = 1);
        } else {
          freqDict[prop] = {};
          freqDict[prop][value] = 1;
        }
      });
    }
  }

  function applyFilters(search, time, filterCfg) {
    let startingPoint = [...dataMeta.data];

    if (search && search.length > 2) {
      startingPoint = startingPoint.filter((paper) =>
        (paper?.Name ?? "").toLowerCase().includes(search.toLowerCase())
      );
    }

    if (time?.start > 0) {
      startingPoint = startingPoint.filter(
        (paper) => time.start <= +paper.Year && +paper.Year <= time.end
      );
    }

    const re = new RegExp("([0-9]+)");

    filterCfg.forEach((group) => {
      if (group?.values) {
        if (group.selected && group.selected.length > 0) {
          const selected = group.selected.map((sel) => (re.test(sel) ? sel.split(") ")[1] : sel));
          const res = [];
          startingPoint.forEach((paper) => {
            const val = paper?.[group.name];
            let found = false;
            if (Array.isArray(val)) found = selected.every((p) => val.includes(p));
            else if (typeof val === "string") found = selected.includes(val);
            if (found) res.push(paper);
          });
          startingPoint = res;
        }
      } else if (group?.categories) {
        group.categories.forEach((option) => {
          if (option.selected && option.selected.length > 0) {
            const selected = option.selected.map((sel) => (re.test(sel) ? sel.split(") ")[1] : sel));
            const res = [];
            startingPoint.forEach((paper) => {
              const val = paper?.[option.name];
              let found = false;
              if (Array.isArray(val)) found = selected.every((p) => val.includes(p));
              else if (typeof val === "string") found = selected.includes(val);
              if (found) res.push(paper);
            });
            startingPoint = res;
          }
        });
      }
    });

    const newFreq = {};
    startingPoint.forEach((paper) => {
      Object.entries(paper).forEach(([prop, arrValue]) => freqCount(prop, arrValue, newFreq));
    });
    freq = newFreq;

    filteredData = startingPoint.sort((p1, p2) => (+p1.Year < +p2.Year ? 1 : -1));

    selectTopics = [];
    filterCfg.forEach((f) => {
      if (f && "groupName" in f && Array.isArray(f.categories)) {
        f.categories.forEach((c) => (selectTopics = selectTopics.concat(c.selected ?? [])));
      } else {
        selectTopics = selectTopics.concat(f?.selected ?? []);
      }
    });
  }

  $: applyFilters($searchFilter, $timeFilters, $filterBy);

  function clearSelections() {
    $filterBy.forEach((prop) => {
      if (prop?.values) prop.selected = [];
      else if (prop?.categories) prop.categories.forEach((option) => (option.selected = []));
    });
    $filterBy = $filterBy;
  }

  function toggleView() {
    if ($viewMode === "browser") return;
    if (showVis) {
      showVis = false;
      showPapers = true;
    } else {
      showVis = true;
      showPapers = false;
    }
  }

  $: if (innerWidth >= breakPoint) {
    drawerHidden = false;
    activateClickOutside = false;
    showVis = true;
    showPapers = true;
  } else {
    drawerHidden = true;
    activateClickOutside = true;
    showVis = false;
    showPapers = true;
  }

  // ---------- right pane: cell selection from trend ----------
  $: papersForRight =
    $viewMode === "detail" && $trendSelection?.papers ? $trendSelection.papers : filteredData;

  $: rightTitle =
    $viewMode === "detail" && $trendSelection
      ? `${$trendSelection.dim}: ${$trendSelection.value} (${String($trendSelection.year)})`
      : null;
</script>

<svelte:head>
  <title>{structure.topView.title}</title>
</svelte:head>

<svelte:window bind:innerWidth bind:innerHeight />

<div class="app-shell">
  <Header
    topView={structure.topView}
    {freq}
    closeFn={() => (drawerHidden = !drawerHidden)}
    toggleParams={{
      hidden: innerWidth >= breakPoint,
      func: toggleView,
      vis: showVis,
      papers: showPapers
    }}
    showTitle={drawerHidden}
    {headerPx}
    drawerHidden={drawerHidden}
  />

  <Drawer
    class="drawer-fix"
    transitionType="fly"
    {backdrop}
    {transitionParams}
    bind:hidden={drawerHidden}
    bind:activateClickOutside={activateClickOutside}
    id="sidebar"
  >
    <div class="flex justify-between items-center">
      <Heading tag="h5">{structure.topView.title}</Heading>
      <Button pill outline size="xs" class="!p-1" on:click={() => (drawerHidden = !drawerHidden)}>
        <CloseSolid class="w-4 h-4" />
      </Button>
    </div>

    <hr style="margin: 15px" />

    <div class="fliter-papers">
      <Heading tag="h6">Filters:</Heading>
      <Button pill outline class="!p-1 border-0" size="xs" on:click={clearSelections}>
        <ReplyOutline class="w-5 h-5" />
      </Button>
    </div>

    <div class="m-5">
      <SearchField />
    </div>

    <FilterPanel {freq} {selectTopics} {filteredData} data={dataMeta.data} />
  </Drawer>

  <main class="main" style="margin-left:{mainLeft}px;">
    <Splitpanes style="height:{mainHeight}px;width:{mainWidth}px;">
      <Pane size={$viewMode === "detail" && showPapers ? 70 : 100}>
  <div class="pane-fill">
    <div class="pane-scroll">
      {#if $viewMode === "browser"}
        <GraphView data={filteredData} {meta} {structure} />
      {:else}
       <DetailView data={filteredData} allData={dataMeta.data} {meta} {structure} />
      {/if}
    </div>
  </div>
</Pane>




      {#if $viewMode === "detail" && showPapers}
        <Pane>
          <div class="num-papers">
            <div class="flex items-center justify-between w-full">
              <P class="m-0">
                Number of papers: {papersForRight.length}/{dataMeta.data.length}
                {#if rightTitle}
                  <span style="margin-left:10px; opacity:.8;">• {rightTitle}</span>
                {/if}
              </P>

              {#if $trendSelection}
                <Button
                  size="xs"
                  pill
                  outline
                  class="!py-1 !px-2"
                  on:click={() => trendSelection.set(null)}
                >
                  Clear
                </Button>
              {/if}
            </div>
          </div>

          <div class="card-container">
            {#each papersForRight as paper, i}
              <PaperCard index={i} {paper} {structure} {meta} />
            {/each}
          </div>
        </Pane>
      {/if}
    </Splitpanes>
  </main>
</div>

<style>
  /* ---------- Theme tokens on body ---------- */
  :global(html),
  :global(body) {
    --app-bg: #0b1320;
    --panel-bg: #162233;
    --panel-bg-2: #101a2a;
    --text: rgba(255, 255, 255, 0.92);
    --text-dim: rgba(255, 255, 255, 0.72);
    --border: rgba(255, 255, 255, 0.10);
    --card-bg: rgba(255, 255, 255, 0.04);
    --card-border: rgba(255, 255, 255, 0.10);
    --accent: #ff6a3d;

    margin: 0;
    background: var(--app-bg);
    color: var(--text);
  }

  :global(body.light) {
    --app-bg: #456266;
    --panel-bg: #90b1b4;
    --panel-bg-2: #789699;
    --text: rgba(10, 30, 30, 0.92);
    --text-dim: rgba(10, 30, 30, 0.65);
    --border: rgba(10, 30, 30, 0.18);
    --card-bg: rgba(255, 255, 255, 0.6);
    --card-border: rgba(10, 30, 30, 0.18);
    --accent: #ff6a3d;

    background: var(--app-bg);
    color: var(--text);
  }

  /* ---------- App shell ---------- */
  .app-shell {
    min-height: 100vh;
    background: var(--app-bg);
    color: var(--text);
  }

  /* ---------- Layering ---------- */
  :global(header) {
    position: relative;
    z-index: 30;
    overflow: visible;
  }
  :global(.drawer-fix) {
    z-index: 60;
  }

  :global(header .navbar),
  :global(header nav) {
    background: var(--panel-bg-2) !important;
    color: var(--text) !important;
  }

  :global(#sidebar) {
    background: var(--panel-bg) !important;
    color: var(--text) !important;
  }

  /* ---------- Main ---------- */
  .main {
    background: var(--app-bg);
  }

  :global(.splitpanes) {
    background: var(--app-bg) !important;
  }

  :global(.splitpanes__pane) {
    background: var(--app-bg) !important;
    color: var(--text);
  }

  .num-papers {
    padding: 10px;
    background: var(--panel-bg);
    border-bottom: 1px solid var(--border);
    color: var(--text);
  }

  .card-container {
    height: calc(100% - 44px);
    overflow: auto;
    background: var(--panel-bg);
    color: var(--text);
  }

  .fliter-papers {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .detail-scroll {
  height: 100%;
  overflow: auto;
  overscroll-behavior: contain;
}

.pane-fill{
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.pane-scroll{
  flex: 1;
  min-height: 0;
  overflow: auto;
}



</style>
