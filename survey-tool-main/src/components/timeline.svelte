<script>
  import RangeSlider from "svelte-range-slider-pips";
  import { P } from "flowbite-svelte";
  import { timeFilters } from "../store";
  import * as d3 from "d3";

  export let data = [];
  export let filteredData = [];

  let minYear = 0;
let maxYear = 0;

let value = [0, 0];

$: if (Array.isArray(data) && data.length > 0) {
  const extent = d3.extent(data, (d) => (d.Year && +d.Year ? Number(d.Year) : undefined));
  minYear = extent[0] ?? 0;
  maxYear = extent[1] ?? 0;

  if (value[0] === 0 && value[1] === 0) {
    value = [minYear, maxYear];
    timeFilters.set({ start: minYear, end: maxYear });
  }
}


  $: value =
    minYear != null && maxYear != null
      ? [$timeFilters.start ?? minYear, $timeFilters.end ?? maxYear]
      : [0, 0];

  function onRangeUpdate() {
    if (minYear == null || maxYear == null) return;
    timeFilters.set({ start: value[0], end: value[1] });
  }

  const padding = { top: 3, bottom: 3, left: 3, right: 3 };
  const gap = 1;
  const width = 250,
    height = 50;

  const convertData = (arr, min, max) => {
    if (!Array.isArray(arr) || min == null || max == null) return [];
    let res = {};
    for (let i = min; i <= max; i++) res[i] = 0;
    arr.forEach((entry) => {
      if (+entry.Year) res[+entry.Year] += 1;
    });
    return Object.values(res);
  };

  $: binData = convertData(data, minYear, maxYear);
  $: filterBinData = convertData(filteredData, minYear, maxYear);

  $: x = d3.scaleLinear().domain([minYear ?? 0, maxYear ?? 0]).range([0, width]);
  $: y = d3
    .scaleLinear()
    .domain([0, d3.max(binData) ?? 0])
    .range([height - padding.top - padding.bottom, 0]);

  $: bandWidth =
    binData.length > 0
      ? (1.0 / binData.length) * (width - padding.left - padding.right) - gap
      : 0;

  $: color = (i) => {
    if (minYear == null) return "#808080";
    let year = i + minYear;
    if (year < value[0] || year > value[1]) return "#808080";
    return "var(--primary)";
  };
</script>

<div class="timeline-container">
	<div class="date-range">
		<P>{value[0]}</P>
		<P>{value[1]}</P>
	</div>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	{#if minYear != null && maxYear != null}
  <RangeSlider
    range
    bind:values={value}
    min={minYear}
    max={maxYear}
    step={1}
    pushy
    on:stop={() => onRangeUpdate()}
  />
{/if}


	<div class="chart">
		<svg width={width} height={height}>
			<g>
				{#each binData as d, i}
					<g >
						<rect id="rect-{i}"
							x={i * (bandWidth + gap) + padding.left} 
							y={y(filterBinData[i]) + padding.bottom}
							width={bandWidth}
							height={height - y(filterBinData[i])  - padding.bottom - padding.top}
							fill={color(i)}>
							<title>Year:{minYear + i} Total:{filterBinData[i]}</title>		
					</rect>
						<rect
							x={i * (bandWidth + gap) + padding.left}
							y={y(d) + padding.bottom}
							width={bandWidth}
							height={height - y(d) - padding.bottom - padding.top}
							stroke-width="{gap}px"
							fill={'none'}

						>
						<title>Year:{minYear + i} Total:{filterBinData[i]}</title>
						</rect>
					</g>					
				{/each}
			</g>
		</svg>
	</div>
</div>

<style>
	.date-range {
		padding-left: 10px;
		padding-right: 10px;
		display: flex;
		justify-content: space-between;
	}
	.chart {
		padding-left: 20px;
	}
</style>
