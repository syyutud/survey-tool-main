import { writable } from "svelte/store";

export const filterBy = writable([]);
export const timeFilters = writable({ start: 0, end: 9999 });
export const searchFilter = writable("");
export const themeMode = writable("dark");
export const urlParams = writable(new URLSearchParams(window.location.search));
export const viewMode = writable("browser"); 
export const detailTool = writable("correlation"); 
export const hoveredPaperKey = writable(null);
export const trendSelection = writable(null);

let prevUrl = undefined;
setInterval(() => {
  const currUrl = window.location.href;
  if (currUrl !== prevUrl) {
    prevUrl = currUrl;
    urlParams.set(new URLSearchParams(window.location.search));
  }
}, 60);
