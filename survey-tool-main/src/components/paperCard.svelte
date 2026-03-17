<script>
  import { Card, Button, Modal } from "flowbite-svelte";
  import { LinkSolid, CopySolid } from "flowbite-svelte-icons";
  import { Tooltip } from "flowbite-svelte";
  import { copyText } from "svelte-copy";
  import PaperDetail from "./paperDetail.svelte";

  import { hoveredPaperKey } from "../store";

  export let paper;
  export let structure;
  export let meta;
  export let index;

  let open = false;
  $: myKey =
    (paper?.DOI ?? "").trim() !== ""
      ? `doi:${(paper.DOI ?? "").trim()}`
      : `name:${paper?.Name ?? ""}-${paper?.Year ?? ""}`;

  function openDoi(p) {
    const doi = (p?.DOI ?? "").trim();
    if (!doi) return;
    window.open(doi.startsWith("10") ? "https://doi.org/" + doi : doi);
  }
</script>

<Tooltip trigger="click" triggeredBy={"#entry-" + index} placement="left"
  >Copied Bibtex to clipboard!</Tooltip
>

<Modal
  class="paper-modal"
  title="Paper Details"
  size="lg"
  id="modal"
  bind:open={open}
  outsideclose
  autoclose={false}
>
  <PaperDetail {paper} detailView={structure.detailView} {meta} />
</Modal>

<Card
  on:click={() => (open = true)}
  class="paper-card w-full m-1 {$hoveredPaperKey === myKey ? 'highlight-paper' : ''}"
  style="cursor: pointer; max-width: 95%; float: right"
  padding="none"
>

  <div class="grid grid-cols-7">
    <div class="ml-2 col-span-6">
      <span class="paper-title">
        {paper.Name}
        <span class="paper-year">{paper.Year}</span>
      </span>
    </div>

    <div>
      <Button
        on:click={(event) => {
          event.stopPropagation();
          openDoi(paper);
        }}
        outline={true}
        size="xs"
        pill={true}
        class="!p-2 mb-2 mr-0.5 border-0 float-right"
      >
        <LinkSolid class="w-4 h-4" />
      </Button>

      {#if paper.Bibtex}
        <Button
          id={"entry-" + index}
          on:click={(event) => {
            event.stopPropagation();
            copyText(paper.Bibtex);
          }}
          outline={true}
          size="xs"
          pill={true}
          class="!p-2 mb-2 mr-1 border-0 float-right"
        >
          <CopySolid class="w-4 h-4" />
        </Button>
      {/if}
    </div>
  </div>
</Card>


<style>
:global(.paper-card > div),
:global(.paper-card > div > div) {
  background: var(--card-bg) !important;
}
:global(.paper-card),
:global(.paper-card .bg-white),
:global(.paper-card .dark\:bg-gray-800),
:global(.paper-card .dark\:bg-gray-900) {
  background: var(--card-bg) !important;
  border: 1px solid var(--card-border) !important;
  color: var(--text) !important;
}

:global(.paper-card .paper-year),
:global(.paper-card .text-gray-400) {
  color: var(--text-dim) !important;
}

:global(.paper-modal [role="dialog"] .bg-white),
:global(.paper-modal [role="dialog"] .dark\:bg-gray-700) {
  background: var(--panel-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}

:global(.paper-modal [role="dialog"] .border-b),
:global(.paper-modal [role="dialog"] .dark\:border-gray-600) {
  background: var(--panel-bg-2) !important;
  border-color: var(--border) !important;
}

:global(.paper-modal [role="dialog"] .p-6),
:global(.paper-modal [role="dialog"] .p-4) {
  background: var(--panel-bg) !important;
  color: var(--text) !important;
}


  .highlight-paper {
    background-color: #fff59d !important; /* 荧光黄 */
    box-shadow: 0 0 0 3px rgba(255, 235, 59, 0.8);
  }

  .dark .highlight-paper {
    background-color: #5c5300 !important; /* dark 模式不刺眼 */
  }
</style>
