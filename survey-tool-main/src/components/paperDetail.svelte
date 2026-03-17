<script>
	import { copyText } from 'svelte-copy';
	import Multiselect from './multiselect.svelte';
	import { Tooltip, Button, Heading, A } from 'flowbite-svelte';
	import { LinkSolid, CopySolid} from 'flowbite-svelte-icons';

	export let paper;
	export let detailView;
	export let meta;
	  $: metaMap = Array.isArray(meta)
    ? Object.fromEntries(meta.map(m => [m.name, m]))
    : (meta || {});


</script>


<!-- {#if paper.image}
	<div style={"padding-right:10px"}>
			<img src={paper.image ? paper.image : "/images/defaultImage.png"} 
					width="200" height=200
					alt={paper.altImage ? paper.altImage: "Image from the paper"}
					/>
	</div>
{/if} -->
<div class="paper-detail">
	<Heading tag="h4" style="margin: 0 20px 0 0 ;">
		{paper.Name} ({paper.Year})
	</Heading>
	<Heading tag="h6" style="margin: 0 0 10px; color: #888;">
		by {(Array.isArray(paper?.Authors) ? paper.Authors : []).join(", ")}
	</Heading>

	{#each (Array.isArray(detailView?.show) ? detailView.show : []) as prop}
		{#if metaMap[prop].type === 'String'}
			<div class="string-select">
				<div><strong>{prop}:&nbsp;</strong></div>
				<div>{paper[prop]}</div>
			</div>
		{:else if metaMap[prop].type === 'MultiSelect'}
			<div class="multi-select">
				<div><strong>{prop}:&nbsp</strong></div>
				{#if Array.isArray(paper?.[prop]) && paper[prop].length > 0 && paper[prop][0] !== ''}
					<Multiselect list={paper[prop]} />
				{/if}
			</div>
		{/if}
	{/each}
	
	<br> 
	<div> 
		<Button on:click={
			(event) => {
				const doi = (paper?.DOI ?? "").trim();
if (!doi) return;
window.open(doi.startsWith("10") ? `https://doi.org/${doi}` : doi);

			}
		} outline class="border-0">
			<LinkSolid class="w-4 h-4"/> &nbsp {paper.DOI} 
		</Button>
		
	
		<Button outline id="copyBibtex" class="border-0" on:click={(e)=>{copyText(paper.Bibtex);}}>
			<CopySolid class="w-4 h-4"/>
			<span>&nbsp Bibtex</span>
		</Button>
	
		<Tooltip trigger="click" triggeredBy="#copyBibtex" placement="right">Copied Bibtex</Tooltip>
	</div>
</div>


<style>
    :global(.paper-modal [role="dialog"]) {
  background: var(--panel-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}

:global(.paper-modal [role="dialog"] header) {
  background: var(--panel-bg) !important;
  border-color: var(--border) !important;
}

:global(.paper-modal [role="dialog"] .p-6),
:global(.paper-modal [role="dialog"] .p-4) {
  background: var(--panel-bg) !important;
  color: var(--text) !important;
}

	.multi-select {
		display: flex;
		align-items: center;
		justify-content: flex-start;
		flex-wrap: wrap;
		align-content: flex-start;
		padding: 2px 0px 2px 0px;
	}
	.string-select {
		height: auto;
		min-height: 40px;
		white-space: pre-wrap;
		word-break: break-word;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		align-content: flex-start;
	}
	.row {
      display: grid;
      grid-template-columns: 180px 1fr; /* 左 label 右 value */
      gap: 10px;
      align-items: start;
     }

	.paper-detail{
        background: var(--panel-bg);
        color: var(--text);
        padding: 16px 18px;
        border-radius: 12px;
     }


</style>
