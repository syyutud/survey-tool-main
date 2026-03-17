<script>
  import { Modal } from "flowbite-svelte";
  import PaperDetail from "../components/paperDetail.svelte";
  import { hoveredPaperKey } from "../store";

  export let data = [];
  export let meta = {};
  export let structure = {};

  let showLinks = true;
  let showKeywords = true;
  let q = "";
  let open = false;
  let activePaper = null;
  let showImages = true;

  const paperKey = (p) => {
    const doi = (p?.DOI ?? "").trim();
    return doi ? `doi:${doi}` : `name:${p?.Name ?? ""}-${p?.Year ?? ""}`;
  };

  function paperUrl(p) {
    const doi = (p?.DOI || "").trim();
    if (!doi) return "";
    return doi.startsWith("10") ? `https://doi.org/${doi}` : doi;
  }

  function paperKeywords(p) {
  if (!p) return [];
  const v = p["Author Keywords"];

  if (Array.isArray(v)) return v.filter(Boolean).map((x) => String(x).trim()).filter(Boolean);
  if (typeof v === "string") {
    return v
      .split(/[;,]/)
      .map((x) => x.trim())
      .filter(Boolean);
  }

  return [];
}

 
  function paperImage(p) {
    const candidates = [
      p?.ImageURL,
      p?.Image,
      p?.ThumbnailURL,
      p?.Thumbnail,
      p?.Figure,
      p?.FigureURL
    ];
    for (const c of candidates) {
      const s = (c ?? "").toString().trim();
      if (s) return s;
    }
    return "";
  }

  function openDetail(p) {
    activePaper = p;
    open = true;
  }

  function closeDetail() {
    open = false;
    activePaper = null;
  }

 
  function matchPaper(p, query) {
    const text = [
    p?.Name,
    p?.DOI,
    p?.Year,
    ...(Array.isArray(p?.Authors) ? p.Authors : []),
    ...(Array.isArray(p?.["Author Keywords"]) ? p["Author Keywords"] : [])
   ]
   .filter(Boolean)
   .join(" ")
   .toLowerCase();

    const terms = query
      .toLowerCase()
      .split(/\s+/)
      .map((x) => x.trim())
      .filter(Boolean);

    if (terms.length === 0) return true;
    return terms.every((t) => text.includes(t));
  }

  $: papers = Array.isArray(data) ? data : [];
  $: papersShown = q.trim() ? papers.filter((p) => matchPaper(p, q.trim())) : papers;
</script>

<Modal title="Paper Details" size="lg" bind:open={open} outsideclose autoclose={false} on:close={closeDetail}>
  {#if activePaper}
    <PaperDetail
      paper={activePaper}
      detailView={structure?.detailView}
      meta={meta}
    />
  {/if}
</Modal>

<div class="graph-content">
  <div class="gv-toolbar">
    <input
      class="gv-search"
      placeholder="Search papers (title / DOI / year / author / topic)..."
      bind:value={q}
    />

    <div class="gv-toggles">
      <button
        class="gv-toggle"
        class:toggle-on={showLinks}
        on:click={() => (showLinks = !showLinks)}
        type="button"
      >
        Links
      </button>

      <button
        class="gv-toggle"
        class:toggle-on={showKeywords}
        on:click={() => (showKeywords = !showKeywords)}
        type="button"
      >
        Keywords
      </button>

      <button class:toggle-on={showImages} 
      class="gv-toggle" 
      on:click={() => (showImages = !showImages)}>
        Images
      </button>


      {#if q.trim().length}
        <button class="gv-clear" on:click={() => (q = "")} type="button">Clear</button>
      {/if}
    </div>
  </div>

  {#if papersShown.length === 0}
    <div class="empty-state">
      No papers match “{q}”.
    </div>
  {:else}
    <div class="grid">
      {#each papersShown as paper, i (paperKey(paper))}
        <div
          class="paper-card"
          on:mouseenter={() => hoveredPaperKey.set(paperKey(paper))}
          on:mouseleave={() => hoveredPaperKey.set(null)}
        >
          {#if showImages}
  <button
    class="image-slot"
    type="button"
    on:click={() => openDetail(paper)}
  >
    {#if paperImage(paper)}
      <img
        src={paperImage(paper)}
        alt="paper thumbnail"
        loading="lazy"
      />
    {:else}
      <div class="placeholder">
        <div class="ph-title">No image</div>
        <div class="ph-sub">Add ImageURL in survey-data</div>
      </div>
    {/if}
  </button>
{/if}


          <div class="paper-meta">
            <div class="title">
              {paper.Name || "Untitled"} <span class="year">{paper.Year || ""}</span>
            </div>

            {#if showLinks}
              <div class="url">
                {#if paperUrl(paper)}
                  <a href={paperUrl(paper)} target="_blank" rel="noreferrer">{paperUrl(paper)}</a>
                {:else}
                  <span class="empty">URL: (empty)</span>
                {/if}
              </div>
            {/if}

            {#if showKeywords}
              <div class="keywords">
                {#if paperKeywords(paper).length > 0}
                  keywords: {paperKeywords(paper).slice(0, 6).join(", ")}
                {:else}
                  <span class="empty">keywords: (empty)</span>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .graph-content {
    padding: 10px 20px;
    background: var(--app-bg);
    color: var(--text);
    height: 100%;
    min-height: 0;
    overflow-y: auto;
  }

  .gv-toolbar {
    position: sticky;
    top: 0;
    z-index: 5;
    padding: 10px 0 12px;
    margin-bottom: 6px;
    background: var(--app-bg);
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .gv-search {
    flex: 1;
    min-width: 240px;
    height: 36px;
    padding: 0 12px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.10);
    color: var(--text);
    outline: none;
  }
  .gv-search::placeholder { opacity: 0.65; }

  .gv-toggles {
    display: flex;
    gap: 8px;
    align-items: center;
    flex: 0 0 auto;
  }

  .gv-toggle, .gv-clear {
    height: 32px;
    padding: 0 10px;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.10);
    background: rgba(255, 255, 255, 0.03);
    color: var(--text);
    cursor: pointer;
    font-weight: 650;
  }

  .gv-toggle.toggle-on {
    border-color: rgba(255, 106, 61, 0.55);
    box-shadow: 0 0 0 2px rgba(255, 106, 61, 0.12) inset;
  }

  .empty-state{
    margin-top: 18px;
    opacity: 0.75;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 14px;
    padding-bottom: 24px;
  }

  .paper-card {
    font-size: 11px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 10px;
  }

  .image-slot {
    width: 100%;
    position: relative;
    height: 140px;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.02);
    cursor: pointer;
    padding: 0;
  }

  .image-slot img{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .placeholder{
    width: 100%;
    height: 100%;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:6px;
    opacity:0.8;
  }

  .ph-title{
    font-weight: 750;
    color: rgba(255,255,255,0.9);
  }
  .ph-sub{
    font-size: 11px;
    opacity: 0.7;
  }

  .paper-meta {
    color: var(--text-dim);
    line-height: 1.35;
  }

  .title {
    color: var(--text);
    font-weight: 600;
    margin-bottom: 4px;
  }

  .year {
    margin-left: 6px;
    opacity: 0.75;
  }

  .url a {
    color: var(--text);
    word-break: break-all;
    text-decoration: underline;
  }

  .empty {
    opacity: 0.75;
  }
</style>
