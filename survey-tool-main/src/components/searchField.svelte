<script>
  import { Input, CloseButton } from "flowbite-svelte";
  import { SearchOutline } from "flowbite-svelte-icons";
  import { searchFilter } from "../store";

  function clearSearch() {
    $searchFilter = "";
  }
</script>

<div class="solo-container solo-container-prop">
  <div class="search-wrap">
    <Input bind:value={$searchFilter} placeholder="Search">
      <SearchOutline slot="left" />
      <CloseButton slot="right" on:click={clearSearch} />
    </Input>
  </div>
</div>

<style>
  .solo-container {
    margin-right: 5px;
    margin-left: 5px;
    width: 100%;
  }

  .solo-container-prop {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .search-wrap {
    width: 100%;
  }

  :global(.search-wrap input) {
    background: var(--panel-bg-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
  }

  :global(.search-wrap input::placeholder) {
    color: var(--text-dim) !important;
  }

  :global(.app-shell.light .search-wrap input) {
    background: #ffffff !important;
    color: rgba(20, 20, 20, 0.92) !important;
    border: 1px solid rgba(20, 20, 20, 0.18) !important;
  }

  :global(.app-shell.light .search-wrap input::placeholder) {
    color: rgba(20, 20, 20, 0.55) !important;
  }
</style>
