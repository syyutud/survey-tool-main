<script>
  import { Navbar, NavBrand, Button, Tooltip, Modal, Heading, A, Li } from "flowbite-svelte";
  import { Dropdown, DropdownItem } from "flowbite-svelte";

  import {
    AdjustmentsHorizontalSolid,
    PlusOutline,
    GithubSolid,
    QuestionCircleOutline,
    SunOutline,
    MoonOutline
  } from "flowbite-svelte-icons";

  import { themeMode, viewMode, detailTool } from "./store";
  import AddEntry from "./components/addEntry.svelte";
  import surveys from "./data/other-surveys.json";

  export let topView;
  export let freq;
  export let closeFn;
  export let toggleParams;
  export let showTitle = true;
  export let drawerHidden = true;
  export let headerPx = 45;

  let openAdd = false;
  let openAbout = false;

  $: isLight = $themeMode === "light";
  const toggleTheme = () => {
  const next = isLight ? "dark" : "light";
  themeMode.set(next);
  document.body.classList.toggle("light", next === "light");
};

</script>

<header style="max-height:{headerPx}px; overflow: visible;">
  <Navbar
    class="mx-0 headerbar"
    style="height:{headerPx}px; overflow: visible;"
  >
    <!-- Left -->
    <div class="flex items-center gap-2">
      {#if drawerHidden}
  <Button pill outline class="!p-1 border-0" on:click={closeFn}>
    <AdjustmentsHorizontalSolid />
    <Tooltip placement="bottom">Toggle Filters</Tooltip>
  </Button>
{/if}

      <Tooltip triggeredBy="#toggle-filters" placement="bottom">
        Toggle Filters
      </Tooltip>

      {#if showTitle}
        <NavBrand>
          <Heading tag="h6">{topView.title}</Heading>
        </NavBrand>
      {/if}
    </div>
    
    <div class="flex items-center gap-2">
      <Button
        pill
        outline
        class="!px-3 !py-1 !text-sm leading-none"
        id="browser-view-btn"
        on:click={() => viewMode.set("browser")}
      >
        Browser View
      </Button>

      <Button
        pill
        outline
        class="!px-3 !py-1 !text-sm leading-none"
        id="detail-view-btn"
        on:click={() => viewMode.set("detail")}
      >
        Detail View <span class="chev">▾</span>
      </Button>

      <Dropdown triggeredBy="#detail-view-btn" placement="bottom" class="min-w-[220px]">
        <DropdownItem
          on:click={() => {
            viewMode.set("detail");
            detailTool.set("correlation");
          }}
        >
          Correlation Matrix
        </DropdownItem>

        <DropdownItem
          on:click={() => {
            viewMode.set("detail");
            detailTool.set("overtheyear");
          }}
        >
          Over the Year
        </DropdownItem>

        <DropdownItem
          on:click={() => {
            viewMode.set("detail");
            detailTool.set("trend");
          }}
        >
          Trend Analysis
        </DropdownItem>
      </Dropdown>
    </div>

    <!-- Right -->
    <div class="flex items-center gap-2">
      <Button
        pill
        outline
        class="!p-1 border-0"
        id="add-entry"
        on:click={() => (openAdd = true)}
      >
        <PlusOutline />
      </Button>
      <Tooltip triggeredBy="#add-entry" placement="bottom">Add entry</Tooltip>

      <Button pill outline class="!p-1 border-0" id="github-link">
        <GithubSolid />
      </Button>
      <Tooltip triggeredBy="#github-link" placement="bottom">GitHub</Tooltip>

      <Button
        pill
        outline
        class="!p-1 border-0"
        id="about-btn"
        on:click={() => (openAbout = true)}
      >
        <QuestionCircleOutline />
      </Button>
      <Tooltip triggeredBy="#about-btn" placement="bottom">About</Tooltip>

      <Button
        pill
        outline
        class="!p-1 border-0"
        id="theme-btn"
        on:click={toggleTheme}
      >
        {#if isLight}
          <MoonOutline />
        {:else}
          <SunOutline />
        {/if}
      </Button>
      <Tooltip triggeredBy="#theme-btn" placement="bottom">
        {isLight ? "Dark mode" : "Light mode"}
      </Tooltip>
    </div>
  </Navbar>
</header>

<!-- Add entry modal -->
<Modal bind:open={openAdd} title="Add entry" size="lg" autoclose={false}>
  <AddEntry detailView={[]} freq={freq} addEntryInfo={topView.addEntry} />
</Modal>

<!-- About modal -->
<Modal bind:open={openAbout} title="About this survey" size="lg">
  <p>{topView.description}</p>
  <p>Authors: {topView.authors}</p>

  <hr class="my-3" />

  <p>Looking for more interactive surveys?</p>
  <ul>
    {#each surveys as s}
      <Li><A href={s.url} target="_blank">{s.name}</A></Li>
    {/each}
  </ul>
</Modal>

<style>
  :global(.headerbar) {
    background: var(--panel-bg);
    color: var(--text);
    border-bottom: 1px solid var(--border);
  }
  .chev { margin-left: 6px; opacity: .85; font-size: 28px; }
</style>
