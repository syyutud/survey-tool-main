<script>
  import { blend_colors, defaultColors } from "./util.js";
  import { ZoomSvg } from "svelte-parts/zoom";
  import { filterBy } from "../store";

  export let allData = [];

  const TOP_TECH_GROUP = "Technology";
  const TOP_TAX_GROUP = "Taxonomy";
 const TECH_X_CATES = ["MR Devices", "2D Devices"];
const TAX_Y_CATES = new Set([
    "Configuration",
    "Temporal",
    "Relationship",
    "Range",
    "Device Dependency",
    "Interaction Dynamics",
    "Space",
    "Anchoring"
  ]);

  const arr = (x) => (Array.isArray(x) ? x : []);
  const asList = (v) => {
    if (Array.isArray(v)) return v.filter(Boolean).map((s) => String(s).trim()).filter(Boolean);
    if (typeof v === "string") {
      const t = v.trim();
      if (!t) return [];
      return t.split(/[;,]/).map((x) => x.trim()).filter(Boolean);
    }
    return [];
  };

  const config = {
    boxSize: 20,
    gap: 6,
    dash: "6 8"
  };

  const padding = { top: 170, right: 230, bottom: 150, left: 290 };

  let maxColorValue = 10;
  let horBarId = -1;
  let verBarId = -1;

  function columnSpacing(i) {
    return padding.left + i * (config.boxSize + config.gap);
  }
  function modelRow(j) {
    return j * (config.boxSize + config.gap) + padding.top;
  }
  function highlight(event, hor, ver) {
    horBarId = hor;
    verBarId = ver;
    event?.preventDefault?.();
  }

  function findGroup(filterCfg, groupName) {
    return (
      arr(filterCfg).find(
        (f) => f && typeof f === "object" && "groupName" in f && f.groupName === groupName
      ) ?? null
    );
  }

  function buildSelectionMap(filterByArr) {
    const map = new Map();
    arr(filterByArr).forEach((g) => {
      if (!g || !(typeof g === "object") || !("groupName" in g)) return;
      arr(g.categories).forEach((c) => {
        const name = c?.name ?? "";
        const sel = arr(c?.selected).map(String);
        if (!name || sel.length === 0) return;
        if (!map.has(name)) map.set(name, new Set());
        sel.forEach((v) => map.get(name).add(v));
      });
    });
    return map;
  }

  function applyFilters(papers, filterByArr) {
    const selectionMap = buildSelectionMap(filterByArr);
    if (selectionMap.size === 0) return arr(papers);

    return arr(papers).filter((paper) => {
      for (const [cateName, selSet] of selectionMap.entries()) {
        const vals = asList(paper?.[cateName]);
        let hit = false;
        for (const v of vals) {
          if (selSet.has(String(v))) {
            hit = true;
            break;
          }
        }
        if (!hit) return false;
      }
      return true;
    });
  }

  function buildXAxis(filterCfg) {
    const g = findGroup(filterCfg, TOP_TECH_GROUP);
    const cats = arr(g?.categories);
    const groupColor = g?.color ?? defaultColors[0];

    const useCats = TECH_X_CATES
      ? TECH_X_CATES.map((n) => cats.find((c) => c?.name === n)).filter(Boolean)
      : cats;

    let xAxis = [];
    const cateSepX = [];

    useCats.forEach((cate) => {
      const cateName = cate?.name ?? "";
      if (!cateName) return;

      const start = xAxis.length;
      arr(cate.values)
        .map((v) => String(v).trim())
        .filter(Boolean)
        .forEach((v) => {
          xAxis.push({ cateName, value: v, key: `${cateName}::${v}`, color: groupColor });
        });

      const end = xAxis.length - 1;
      if (end >= start) cateSepX.push({ groupName: cateName, line: [start, end] });
    });

    return { xAxis, cateSepX };
  }

  function buildYAxis(filterCfg) {
    const g = findGroup(filterCfg, TOP_TAX_GROUP);
    const cats = arr(g?.categories);
    const groupColor = g?.color ?? defaultColors[1];

    const useCats = TAX_Y_CATES ? cats.filter((c) => TAX_Y_CATES.has(c?.name ?? "")) : cats;

    let yAxis = [];
    const cateSepY = [];

    useCats.forEach((cate) => {
      const cateName = cate?.name ?? "";
      if (!cateName) return;

      const start = yAxis.length;
      arr(cate.values)
        .map((v) => String(v).trim())
        .filter(Boolean)
        .forEach((v) => {
          yAxis.push({ cateName, value: v, key: `${cateName}::${v}`, color: groupColor });
        });

      const end = yAxis.length - 1;
      if (end >= start) cateSepY.push({ groupName: cateName, line: [start, end] });
    });

    return { yAxis, cateSepY };
  }

  function buildMatrix(xAxis, yAxis, papers) {
    const matrix = Array.from({ length: xAxis.length }, () => new Array(yAxis.length).fill(0));
    const paperCountX = new Array(xAxis.length).fill(0);
    const paperCountY = new Array(yAxis.length).fill(0);

    const neededCols = new Set([...xAxis.map((a) => a.cateName), ...yAxis.map((a) => a.cateName)]);
    const cache = arr(papers).map((p) => {
      const o = {};
      neededCols.forEach((k) => (o[k] = asList(p?.[k])));
      return o;
    });

    xAxis.forEach((x, i) => {
      cache.forEach((c) => {
        if (c[x.cateName]?.includes(x.value)) paperCountX[i] += 1;
      });
    });

    yAxis.forEach((y, j) => {
      cache.forEach((c) => {
        if (c[y.cateName]?.includes(y.value)) paperCountY[j] += 1;
      });
    });

    xAxis.forEach((x, i) => {
      yAxis.forEach((y, j) => {
        let count = 0;
        cache.forEach((c) => {
          if (c[x.cateName]?.includes(x.value) && c[y.cateName]?.includes(y.value)) count += 1;
        });
        matrix[i][j] = count;
      });
    });

    return { matrix, paperCountX, paperCountY };
  }

  function getMaxCount(x, y) {
    return Math.max(...arr(x), ...arr(y), 1);
  }

  let visData = {
    xAxis: [],
    yAxis: [],
    matrix: [],
    cateSepX: [],
    cateSepY: [],
    paperCountX: [],
    paperCountY: []
  };

  $: filteredData = applyFilters(allData, $filterBy);

  $: {
    const { xAxis, cateSepX } = buildXAxis($filterBy);
    const { yAxis, cateSepY } = buildYAxis($filterBy);
    const { matrix, paperCountX, paperCountY } = buildMatrix(xAxis, yAxis, filteredData);

    visData = { xAxis, yAxis, matrix, cateSepX, cateSepY, paperCountX, paperCountY };
    maxColorValue = getMaxCount(paperCountX, paperCountY);
  }

  function gridLeftX() {
    return columnSpacing(0) - config.boxSize / 2;
  }
  function gridRightX() {
    return columnSpacing(visData.xAxis.length - 1) + config.boxSize / 2;
  }
  function gridTopY() {
    return modelRow(0) - config.boxSize / 2;
  }
  function gridBottomY() {
    return modelRow(visData.yAxis.length - 1) + config.boxSize / 2;
  }

  function countColLeftX() {
    return columnSpacing(visData.xAxis.length) - config.boxSize / 2;
  }
  function countColRightX() {
    return columnSpacing(visData.xAxis.length) + config.boxSize / 2;
  }

  function blockTopY(pac) {
    return modelRow(pac.line[0]) - config.boxSize / 2;
  }
  function blockBottomY(pac) {
    return modelRow(pac.line[1]) + config.boxSize / 2;
  }

  function splitX() {
    if (!visData?.cateSepX?.length || visData.cateSepX.length < 2) return null;
    const lastMR = visData.cateSepX[0].line[1];
    return columnSpacing(lastMR) + config.boxSize / 2 + config.gap / 2;
  }

  let w = 100,
    h = 100;
</script>

<div class="corr-root corr-container" bind:clientWidth={w} bind:clientHeight={h}>
  <ZoomSvg viewBox="0 0 {w} {h}">
    <g class="cm-seps" pointer-events="none">
      {#if visData.xAxis.length > 0 && visData.yAxis.length > 0}
        <rect
          x={gridLeftX()}
          y={gridTopY()}
          width={gridRightX() - gridLeftX()}
          height={gridBottomY() - gridTopY()}
          class="cm-frame"
        />
       {#if splitX() !== null}
          <line x1={splitX()} y1={gridTopY()} x2={splitX()} y2={gridBottomY()} class="cm-dash" />
        {/if}

        {#each visData.cateSepY as pac}
          <rect
            x={gridLeftX()}
            y={blockTopY(pac)}
            width={gridRightX() - gridLeftX()}
            height={blockBottomY(pac) - blockTopY(pac)}
            class="cm-dash"
            fill="none"
          />

          <line
            x1={gridLeftX() - 10}
            y1={blockTopY(pac) + 5}
            x2={gridLeftX() - 10}
            y2={blockBottomY(pac) - 5}
            class="cm-accent"
          />

          <path
            class="cm-bracket"
            d="
              M {countColRightX() + 14} {blockTopY(pac)}
              L {countColRightX() + 14} {blockBottomY(pac)}
              M {countColLeftX()} {blockTopY(pac)}
              L {countColRightX() + 14} {blockTopY(pac)}
              M {countColLeftX()} {blockBottomY(pac)}
              L {countColRightX() + 14} {blockBottomY(pac)}
            "
          />
        {/each}
      {/if}
    </g>

    <g class="x-axis">
      {#each visData.xAxis as cate, i}
        <text
          on:mouseover={(e) => highlight(e, -1, i)}
          on:mouseout={(e) => highlight(e, -1, -1)}
          text-anchor="end"
          transform="translate({columnSpacing(i)}, {modelRow(-1) - config.boxSize / 2}) rotate(40)"
          alignment-baseline="middle"
          class="cm-xlabel"
        >
          {cate.value}
        </text>
      {/each}
    </g>

    <g class="y-axis">
      {#each visData.yAxis as cate, j}
        <text
          on:mouseover={(e) => highlight(e, j, -1)}
          on:mouseout={(e) => highlight(e, -1, -1)}
          x={gridLeftX() - 24}
          y={modelRow(j)}
          text-anchor="end"
          alignment-baseline="middle"
          class="cm-ylabel"
        >
          {cate.value}
        </text>
      {/each}
    </g>

    <g class="matrix">
      {#each visData.matrix as row, i}
        {#each row as col, j}
          <g
            on:mouseover={(e) => highlight(e, j, i)}
            on:mouseout={(e) => highlight(e, -1, -1)}
          >
            <rect
              x={columnSpacing(i) - config.boxSize / 2}
              y={modelRow(j) - config.boxSize / 2}
              width={config.boxSize}
              height={config.boxSize}
              fill={blend_colors(visData.xAxis[i].color, visData.yAxis[j].color, 0.7)}
              opacity={col === 0 ? 0 : col / maxColorValue}
              rx="2"
            />
            <text
              x={columnSpacing(i)}
              y={modelRow(j)}
              text-anchor="middle"
              dominant-baseline="central"
              class="cm-cell"
            >
              {col}
            </text>
          </g>
        {/each}
      {/each}
    </g>

    <g class="total-x">
      <text
        x={gridLeftX() - 24}
        y={modelRow(visData.yAxis.length) + config.boxSize / 2}
        text-anchor="end"
        dominant-baseline="central"
        class="cm-countlabel"
      >
        Count:
      </text>

      {#each visData.paperCountX as num, i}
        <g>
          <rect
            x={columnSpacing(i) - config.boxSize / 2}
            y={modelRow(visData.yAxis.length) + config.boxSize / 2 - config.boxSize}
            width={config.boxSize}
            height={config.boxSize}
            fill={visData.xAxis[i].color}
            opacity={num === 0 ? 0 : num / maxColorValue}
            rx="2"
          />
          <text
            x={columnSpacing(i)}
            y={modelRow(visData.yAxis.length) + config.boxSize / 2 - config.boxSize / 2}
            text-anchor="middle"
            dominant-baseline="central"
            class="cm-count"
          >
            {num}
          </text>
        </g>
      {/each}
    </g>

    <g class="total-y">
      <text
        x={columnSpacing(visData.xAxis.length) + config.boxSize / 2}
        y={modelRow(-2)}
        text-anchor="middle"
        dominant-baseline="central"
        class="cm-countlabel"
      >
        Count:
      </text>

      {#each visData.paperCountY as num, j}
        <g>
          <rect
            x={columnSpacing(visData.xAxis.length) - config.boxSize / 2}
            y={modelRow(j) - config.boxSize / 2}
            width={config.boxSize}
            height={config.boxSize}
            fill={visData.yAxis[j].color}
            opacity={num === 0 ? 0 : num / maxColorValue}
            rx="2"
          />
          <text
            x={columnSpacing(visData.xAxis.length)}
            y={modelRow(j)}
            text-anchor="middle"
            dominant-baseline="central"
            class="cm-count"
          >
            {num}
          </text>
        </g>
      {/each}

      {#each visData.cateSepY as pac}
        <text
          x={countColRightX() + 26}
          y={modelRow((pac.line[0] + pac.line[1]) / 2)}
          text-anchor="start"
          alignment-baseline="middle"
          class="cm-block"
        >
          {pac.groupName}
        </text>
      {/each}
    </g>

    {#if verBarId !== -1}
      <rect
        x={columnSpacing(verBarId) - config.boxSize / 2}
        y={gridTopY()}
        width={config.boxSize}
        height={gridBottomY() - gridTopY()}
        class="cm-hover"
      />
    {/if}

    {#if horBarId !== -1}
      <rect
        x={gridLeftX()}
        y={modelRow(horBarId) - config.boxSize / 2}
        width={gridRightX() - gridLeftX()}
        height={config.boxSize}
        class="cm-hover"
      />
    {/if}
  </ZoomSvg>
</div>

<style>
  /* Inherit page typography (Flowbite/Tailwind) */
  .corr-root {
    /* You can tune this if you want the whole matrix smaller/larger without changing code */
    --cm-scale: 1;
    --cm-text: rgba(255, 255, 255, 0.88);
    --cm-text-dim: rgba(255, 255, 255, 0.75);
    --cm-line: rgba(255, 255, 255, 0.22);
    --cm-dash: rgba(255, 255, 255, 0.35);
    --cm-bracket: rgba(255, 255, 255, 0.55);
    --cm-hover: rgba(255, 255, 255, 0.12);
    --cm-accent: var(--accent, #ff6a3d);
  }

  .corr-container {
    width: 100%;
    height: 100%;
  }

  /* labels */
  .cm-xlabel {
    fill: var(--cm-text);
    font-size: calc(12px * var(--cm-scale));
    font-weight: 600;
    user-select: none;
  }

  .cm-ylabel {
    fill: var(--cm-text);
    font-size: calc(14px * var(--cm-scale));
    font-weight: 600;
    user-select: none;
  }

  /* numbers */
  .cm-cell {
    fill: var(--cm-text-dim);
    font-size: calc(11px * var(--cm-scale));
    font-weight: 600;
    pointer-events: none;
    user-select: none;
  }

  .cm-countlabel {
    fill: var(--cm-text-dim);
    font-size: calc(12px * var(--cm-scale));
    font-weight: 700;
    pointer-events: none;
    user-select: none;
  }

  .cm-count {
    fill: var(--cm-text);
    font-size: calc(11px * var(--cm-scale));
    font-weight: 700;
    pointer-events: none;
    user-select: none;
  }

  .cm-block {
    fill: var(--cm-text);
    font-size: calc(15px * var(--cm-scale));
    font-weight: 700;
    pointer-events: none;
    user-select: none;
  }

  /* separators */
  .cm-frame {
    stroke: var(--cm-line);
    stroke-width: 2;
    fill: none;
  }

  .cm-dash {
    stroke: var(--cm-dash);
    stroke-width: 2.5;
    stroke-dasharray: 6 8;
    stroke-linecap: butt;
  }

  .cm-bracket {
    stroke: var(--cm-bracket);
    stroke-width: 4;
    stroke-linecap: round;
    fill: none;
  }

  .cm-accent {
    stroke: var(--cm-accent);
    stroke-width: 4;
    stroke-linecap: round;
  }

  .cm-hover {
    fill: var(--cm-hover);
    pointer-events: none;
  }
</style>