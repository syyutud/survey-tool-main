<script>
  import { onMount, onDestroy, tick } from "svelte";
  import { Button } from "flowbite-svelte";
  import { trendSelection } from "../store";
  import { getYears, getDimValues, buildCellPapers, topKeywords } from "./trendencyUtil.js";
  import structureRaw from "../data/survey-config.json";
  export let data = [];

function pickDefaultDim(meta, data) {
  const metaNames = Array.isArray(meta) ? meta.map(m => m?.name).filter(Boolean) : Object.keys(meta ?? {});
  const candidates = [
    "Topic",
    "Taxonomy",
    "Use Case",
    "Data type",
    "Display type",
    "Interaction",
    ...metaNames
  ];

  const sample = Array.isArray(data) && data.length ? data[0] : {};
  const dataKeys = Object.keys(sample ?? {});
  const all = [...new Set([...candidates, ...dataKeys])];
  for (const k of all) {
    if (!k) continue;
    const has = (Array.isArray(data) ? data : []).some(p => {
      const v = p?.[k];
      return (Array.isArray(v) && v.length) || (typeof v === "string" && v.trim());
    });
    if (has) return k;
  }
  return dataKeys[0] ?? "Year";
}
let _lastDim = null;

$: if (Array.isArray(data) && data.length && dim && (data !== _lastDataRef || dim !== _lastDim)) {
  _lastDataRef = data;
  _lastDim = dim;
  initAxesAndCache();
}

const structure = structureRaw ?? {};
const filterGroups = Array.isArray(structure.filterBy) ? structure.filterBy : [];
const DIM_GROUPS = ["Technology", "Taxonomy", "DISPLAY", "DATA & VIS"];

let dim = "Taxonomy"; 

function getGroupByName(groupName) {
  return filterGroups.find((g) => g?.groupName === groupName);
}

function groupCategoryNames(groupName) {
  const g = getGroupByName(groupName);
  return Array.isArray(g?.categories) ? g.categories.map((c) => c?.name).filter(Boolean) : [];
}

function paperVals(paper, field) {
  const v = paper?.[field];
  if (Array.isArray(v)) return v.filter(Boolean);
  if (typeof v === "string" && v.trim()) return [v.trim()];
  return [];
}


  let years = [];
  let valuesAll = [];
  export let meta = {};
  let pending = new Set(); 
  let applied = new Set(); 
  let rowLocalCenter = new Map();
  let heatWrapEl;
  let lastCellKey = null;

  let pop = {
    open: false,
    x: 0,
    y: 0,
    year: null,
    value: null,
    papers: [],
    prevList: [],
    curList: [],
    nextList: []
  };

  let cellCache = new Map(); 
  let rowStats = new Map(); 
  let globalMin = 0;
  let globalMax = 1;

  let zoom = 1; 
  const zoomIn = () => (zoom = Math.min(1.8, +(zoom + 0.1).toFixed(2)));
  const zoomOut = () => (zoom = Math.max(0.5, +(zoom - 0.1).toFixed(2)));

  const keyOf = (v, y) => `${v}@@${y}`;

  const safeYearNumber = (y) => {
    const n = Number(y);
    return Number.isFinite(n) ? n : y;
  };

  let _lastDataRef = null;

  function initAxesAndCache() {
    years = getYears(data).map(safeYearNumber);
   const cats = groupCategoryNames(dim);
   const s = new Set();
   (data ?? []).forEach((p) => {
    cats.forEach((cn) => paperVals(p, cn).forEach((x) => s.add(x)));
    });
    valuesAll = [...s];


    pending = new Set();
    applied = new Set();
    rowLocalCenter = new Map();

    closePop(true);
    trendSelection.set(null);

    rebuildCache();
  }

 $: if (Array.isArray(data) && data !== _lastDataRef) {
  _lastDataRef = data;
  years = getYears(data).map(safeYearNumber);
  valuesAll = getDimValues(data, dim);
  rebuildCache();
}

  $: valuesShown = applied.size > 0 ? valuesAll.filter((v) => applied.has(v)) : valuesAll;

  function rebuildCache() {
    const newCache = new Map();
    const newRowStats = new Map();

    for (const v of valuesAll) {
      let rMin = Infinity;
      let rMax = -Infinity;
      let rTotal = 0;

      for (const y of years) {
        const cats = groupCategoryNames(dim);
        const papers = (data ?? []).filter((p) => {
         if (Number(p?.Year) !== Number(y)) return false;
          return cats.some((cn) => paperVals(p, cn).includes(v));
          });

        const count = papers.length;
        newCache.set(keyOf(v, y), { papers, count });

        rMin = Math.min(rMin, count);
        rMax = Math.max(rMax, count);
        rTotal += count;
      }

      if (!Number.isFinite(rMin)) rMin = 0;
      if (!Number.isFinite(rMax)) rMax = 0;

      newRowStats.set(v, { min: rMin, max: rMax, total: rTotal });
    }

    cellCache = newCache;
    rowStats = newRowStats;

    let gMin = Infinity;
    let gMax = -Infinity;
    for (const v of valuesAll) {
      for (const y of years) {
        const c = newCache.get(keyOf(v, y))?.count ?? 0;
        gMin = Math.min(gMin, c);
        gMax = Math.max(gMax, c);
      }
    }
    globalMin = Number.isFinite(gMin) ? gMin : 0;
    globalMax = Number.isFinite(gMax) ? gMax : 1;
  }

  $: if (valuesShown && valuesShown.length && years && years.length && cellCache) {
    let gMin = Infinity;
    let gMax = -Infinity;
    for (const v of valuesShown) {
      for (const y of years) {
        const c = cellCache.get(keyOf(v, y))?.count ?? 0;
        gMin = Math.min(gMin, c);
        gMax = Math.max(gMax, c);
      }
    }
    globalMin = Number.isFinite(gMin) ? gMin : 0;
    globalMax = Number.isFinite(gMax) ? gMax : 1;
  }

  function cellInfo(v, y) {
    return cellCache.get(keyOf(v, y)) ?? { papers: [], count: 0 };
  }

  function togglePendingRow(v) {
    if (pending.has(v)) pending.delete(v);
    else pending.add(v);
    pending = new Set(pending);
  }

  function applyPending() {
  applied = new Set(pending);
  closePop(true);

  if (pending.size === 0) {
    trendSelection.set(null);
  } else {
    const paperMap = new Map();

    for (const v of pending) {
      for (const y of years) {
        const papers = cellInfo(v, y).papers ?? [];
        for (const p of papers) {
          const key =
            (p?.DOI ?? "").trim() || `${p?.Name ?? ""}-${p?.Year ?? ""}`;
          paperMap.set(key, p);
        }
      }
    }

    trendSelection.set({
      kind: "rows",
      dim,
      values: [...pending],
      papers: [...paperMap.values()]
    });
  }

  tick().then(() => {
    if (heatWrapEl) heatWrapEl.scrollLeft = 0;
  });
}
  function clearAll() {
    pending = new Set();
    applied = new Set();
    rowLocalCenter = new Map();

    closePop(true);
    trendSelection.set(null);
    lastCellKey = null;

    tick().then(() => {
      if (heatWrapEl) {
        heatWrapEl.scrollTop = 0;
        heatWrapEl.scrollLeft = 0;
      }
    });
  }

  function colorFromMinMax(count, min, max) {
    if (max === min) return "rgba(255,106,61,0.25)";
    const t = (count - min) / (max - min);
    const a = 0.12 + 0.78 * Math.max(0, Math.min(1, t));
    return `rgba(255,106,61,${a})`;
  }
 function colorForRow(v, count) {
    const isLocal = rowLocalCenter.has(v);
    if (!isLocal) return colorFromMinMax(count, globalMin, globalMax);
    const rs = rowStats.get(v) ?? { min: 0, max: 1 };
    return colorFromMinMax(count, rs.min, rs.max);
  }

  function localTrendSymbol(v, y, c) {
    const cPrev = cellInfo(v, y - 1).count ?? 0;
    const cNext = cellInfo(v, y + 1).count ?? 0;

    if (c > cPrev && c >= cNext) return "↑";
    if (c < cPrev && c <= cNext) return "↓";
    return "→";
  }

  function displayValue(v, y, count) {
    const isLocal = rowLocalCenter.has(v);
    if (!isLocal) return count > 0 ? String(count) : "";
    if (count <= 0) return "";
    return localTrendSymbol(v, y, count);
  }

  function closePop(resetLastKey = false) {
    pop = { ...pop, open: false };
    if (resetLastKey) lastCellKey = null;
  }

async function onCellClick(e, v, y) {
  e.stopPropagation();

  const cellKey = keyOf(v, y);
  if (cellKey === lastCellKey) {
    const nm = new Map(rowLocalCenter);
    if (nm.has(v) && nm.get(v) === y) {
      nm.delete(v);
    } else {
      nm.set(v, y);
    }
    rowLocalCenter = nm;
  } else {
    const nm = new Map(rowLocalCenter);
    nm.set(v, y);
    rowLocalCenter = nm;
  }

  lastCellKey = cellKey;

  const cur = cellInfo(v, y).papers ?? [];
  const prev = cellInfo(v, y - 1).papers ?? [];
  const next = cellInfo(v, y + 1).papers ?? [];


  trendSelection.set({
    kind: "cell",
    dim,
    value: v,
    year: y,
    papers: cur
  });

  const rect = heatWrapEl?.getBoundingClientRect();
  const px = rect ? e.clientX - rect.left : e.clientX;
  const py = rect ? e.clientY - rect.top : e.clientY;

  pop = {
    open: true,
    x: px + 12,
    y: py + 12,
    year: y,
    value: v,
    papers: cur,
    prevList: topKeywords(prev, 6),
    curList: topKeywords(cur, 6),
    nextList: topKeywords(next, 6)
  };

  await tick();

  const popEl = document.getElementById("trend-popover");
  if (popEl && rect) {
    const pr = popEl.getBoundingClientRect();
    const maxX = rect.width - pr.width - 8;
    const maxY = rect.height - pr.height - 8;
    pop = {
      ...pop,
      x: Math.max(8, Math.min(pop.x, maxX)),
      y: Math.max(8, Math.min(pop.y, maxY))
    };
  }
}

  function viewRelatedPapers() {
    if (!pop.open) return;
    trendSelection.set({
      kind: "cell",
      dim,
      value: pop.value,
      year: pop.year,
      papers: pop.papers
    });
  }

  function handleGlobalClick() {
    if (pop.open) closePop(false); 
  }

  function handleEsc(e) {
    if (e.key === "Escape") closePop(false); 
  }

  onMount(() => window.addEventListener("keydown", handleEsc));
  onDestroy(() => window.removeEventListener("keydown", handleEsc));
</script>

<div class="trend-root" on:click={handleGlobalClick}>
  <div class="title-row">
    <div class="title-left">
  <div class="h1">Trendency Analysis</div>

  <select
    class="dim-select"
    bind:value={dim}
    on:change={() => initAxesAndCache()}
    title="Choose group dimension"
  >
    {#each DIM_GROUPS as g}
      <option value={g}>{g}</option>
    {/each}
  </select>
</div>


    <div class="zoom-bar">
      <Button size="xs" pill outline on:click={zoomOut}>-</Button>
      <span class="zoom-val">{Math.round(zoom * 100)}%</span>
      <Button size="xs" pill outline on:click={zoomIn}>+</Button>
    </div>
  </div>

  <div class="heat-card">
    <div class="card-title">Global / Focused Heatmap</div>

    <div class="heat-scroll" bind:this={heatWrapEl}>
      <div class="heat-zoom" style="transform: scale({zoom}); transform-origin: top left;">
        <div class="heat-grid" style="grid-template-columns: 320px repeat({years.length}, 72px);">
          <div class="corner"></div>

          {#each years as y}
            <div class="col-head">{y}</div>
          {/each}

          {#each valuesShown as v}
            <div class="row-head {pending.has(v) ? 'row-pending' : ''}">
              <button class="row-toggle" on:click={() => togglePendingRow(v)} title="Select for Apply (pending)">
                <span class="dot {pending.has(v) ? 'dot-on' : ''}"></span>
                <span class="row-text">{v}</span>
              </button>

              <span class="row-mode">
                {#if rowLocalCenter.has(v)}
                  <span class="mode-pill mode-local">LOCAL</span>
                {:else}
                  <span class="mode-pill mode-global">GLOBAL</span>
                {/if}
              </span>
            </div>

            {#each years as yy}
              {@const info = cellInfo(v, yy)}
              <button
                class="cell"
                style="background:{colorForRow(v, info.count)}"
                on:click={(e) => onCellClick(e, v, yy)}
                title={`${v} • ${yy} : ${info.count} papers`}
              >
                {displayValue(v, yy, info.count)}
              </button>
            {/each}
          {/each}
        </div>
      </div>

      {#if pop.open}
        <div
          id="trend-popover"
          class="popover"
          style="left:{pop.x}px; top:{pop.y}px;"
          on:click|stopPropagation
        >
          <div class="pop-head">
            <div class="pop-title">{pop.value} — {pop.year - 1} → {pop.year} → {pop.year + 1}</div>
            <button class="x" on:click={() => closePop(false)}>×</button>
          </div>

          <div class="pop-3col">
            <div class="col">
              <div class="col-title">{pop.year - 1}</div>
              {#if pop.prevList.length === 0}
                <div class="empty">No data</div>
              {:else}
                {#each pop.prevList as k}
                  <div class="kw-row">
                    <span class="kw">{k.key ?? k.keyword ?? k.term}</span>
                    <span class="cnt">{k.count ?? ""}</span>
                  </div>
                {/each}
              {/if}
            </div>

            <div class="col mid">
              <div class="col-title">{pop.year}</div>
              {#if pop.curList.length === 0}
                <div class="empty">No data</div>
              {:else}
                {#each pop.curList as k}
                  <div class="kw-row">
                    <span class="kw">{k.key ?? k.keyword ?? k.term}</span>
                    <span class="cnt">{k.count ?? ""}</span>
                  </div>
                {/each}
              {/if}
            </div>

            <div class="col">
              <div class="col-title">{pop.year + 1}</div>
              {#if pop.nextList.length === 0}
                <div class="empty">No data</div>
              {:else}
                {#each pop.nextList as k}
                  <div class="kw-row">
                    <span class="kw">{k.key ?? k.keyword ?? k.term}</span>
                    <span class="cnt">{k.count ?? ""}</span>
                  </div>
                {/each}
              {/if}
            </div>
          </div>

          <div class="pop-actions">
            <Button size="xs" pill on:click={viewRelatedPapers}>
              View related papers ({pop.papers.length})
            </Button>
          </div>
        </div>
      {/if}
    </div>

    <div class="bottom-bar">
      <div class="bottom-left">
        <Button size="xs" pill on:click={applyPending} disabled={pending.size === 0 && applied.size === 0}>
          Apply ({pending.size})
        </Button>
        <Button
          size="xs"
          pill
          outline
          on:click={clearAll}
          disabled={pending.size === 0 && applied.size === 0 && rowLocalCenter.size === 0}
        >
          Clear
        </Button>
      </div>

      <div class="legend">
        <span>min {globalMin}</span>
        <div class="bar"></div>
        <span>max {globalMax}</span>
      </div>
    </div>
  </div>
</div>

<style>
  .trend-root {
    width: 100%;
    height: 100%;
    padding: 18px;
    background: var(--app-bg);
    color: var(--text);
    overflow: hidden;
  }

  .title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
  }

  .h1 {
    font-size: 26px;
    font-weight: 750;
    line-height: 1.1;
  }

  .zoom-bar {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .zoom-val {
    opacity: 0.8;
    font-size: 12px;
    min-width: 42px;
    text-align: center;
  }

  .heat-card {
    height: calc(100% - 60px);
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 14px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.14);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .card-title {
    font-size: 18px;
    font-weight: 650;
    margin-bottom: 10px;
  }

  .heat-scroll {
    position: relative;
    flex: 1 1 auto;
    overflow: auto;
    border-radius: 14px;
    padding: 8px;
    background: rgba(0, 0, 0, 0.06);
  }

  .heat-zoom {
    display: inline-block;
  }

  .heat-grid {
    display: grid;
    gap: 10px;
    align-items: center;
    justify-items: center;
    padding: 6px 6px 14px;
  }

  .corner {
    width: 100%;
    height: 28px;
  }

  .col-head {
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.85;
    font-weight: 650;
  }

  .row-head {
    width: 100%;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    position: sticky;
    left: 0;
    z-index: 2;
  }

  .row-pending {
    box-shadow: 0 0 0 2px rgba(255, 106, 61, 0.25) inset;
  }

  .row-toggle {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 0;
    background: transparent;
    color: inherit;
    cursor: pointer;
    font-weight: 750;
    text-align: left;
    min-width: 0;
  }

  .row-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 240px;
  }

  .dot {
    width: 12px;
    height: 12px;
    border-radius: 999px;
    border: 2px solid rgba(255, 255, 255, 0.35);
    background: transparent;
    flex: 0 0 auto;
  }

  .dot-on {
    background: var(--accent);
    border-color: var(--accent);
  }

  .row-mode {
    display: flex;
    gap: 8px;
    align-items: center;
    opacity: 0.9;
  }

  .mode-pill {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.6px;
    padding: 4px 8px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .mode-global {
    background: rgba(255, 255, 255, 0.04);
  }

  .mode-local {
    background: rgba(255, 106, 61, 0.12);
    border-color: rgba(255, 106, 61, 0.45);
  }

  .cell {
    width: 64px;
    height: 64px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.92);
    font-weight: 850;
    cursor: pointer;
    transition: transform 0.06s ease, filter 0.1s ease;
  }

  .cell:hover {
    transform: translateY(-1px);
    filter: brightness(1.08);
  }

  .bottom-bar {
    flex: 0 0 auto;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
  }

  .bottom-left {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .legend {
    display: flex;
    align-items: center;
    gap: 10px;
    opacity: 0.88;
    min-width: 380px;
    justify-content: flex-end;
  }

  .bar {
    width: 200px;
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(255, 106, 61, 0.15), rgba(255, 106, 61, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  /* popover */
  .popover {
    position: absolute;
    z-index: 50;
    width: 560px;
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
    overflow: hidden;
  }

  .pop-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
  }

  .pop-title {
    font-weight: 850;
  }

  .x {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    border: 0;
    cursor: pointer;
    background: transparent;
    color: rgba(255, 255, 255, 0.75);
    font-size: 18px;
  }

  .x:hover {
    background: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.95);
  }

  .pop-3col {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    padding: 12px;
  }

  .col {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
    padding: 10px;
    min-height: 180px;
  }

  .col.mid {
    border-color: rgba(255, 106, 61, 0.25);
    box-shadow: 0 0 0 2px rgba(255, 106, 61, 0.08) inset;
  }

  .col-title {
    font-size: 13px;
    font-weight: 850;
    opacity: 0.9;
    margin-bottom: 10px;
  }

  .kw-row {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-size: 13px;
    padding: 6px 8px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    margin-bottom: 6px;
  }

  .kw {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 150px;
  }

  .cnt {
    opacity: 0.85;
    font-weight: 850;
  }

  .empty {
    font-size: 12px;
    opacity: 0.7;
  }

  .pop-actions {
    padding: 0 12px 12px;
    display: flex;
    justify-content: flex-end;
  }
  .title-left{
  display:flex;
  align-items:center;
  gap:12px;
}

.dim-select{
  height:32px;
  padding:0 10px;
  border-radius:10px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.9);
  font-weight: 650;
  outline: none;
}
.dim-select option{
  background: #0b1220;
}

</style>
