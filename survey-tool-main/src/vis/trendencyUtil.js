export function getYears(data) {
  const ys = new Set();
  (data ?? []).forEach((p) => {
    const y = Number(p?.Year);
    if (!Number.isNaN(y)) ys.add(y);
  });
  return Array.from(ys).sort((a, b) => a - b);
}

export function getDimValues(data, dim) {
  const vals = new Set();
  (data ?? []).forEach((p) => {
    const v = p?.[dim];
    if (Array.isArray(v)) v.forEach((x) => x && vals.add(String(x)));
    else if (typeof v === "string" && v.trim()) vals.add(v.trim());
  });
  return Array.from(vals).sort((a, b) => a.localeCompare(b));
}

export function buildCellPapers(data, dim, value, year) {
  const y = Number(year);
  return (data ?? []).filter((p) => {
    const py = Number(p?.Year);
    if (Number.isNaN(py) || py !== y) return false;
    const v = p?.[dim];
    if (Array.isArray(v)) return v.includes(value);
    if (typeof v === "string") return v === value;
    return false;
  });
}

export function topKeywords(papers, k = 6) {
  const freq = new Map();

  const pushToken = (t) => {
    const s = String(t ?? "").trim();
    if (!s) return;
    if (s.toLowerCase() === "not specified") return; 
    freq.set(s, (freq.get(s) ?? 0) + 1);
  };

  (papers ?? []).forEach((p) => {
    const akw =
      p?.["Author Keywords"] ??
      p?.["Author keywords"] ??
      p?.["author keywords"] ??
      p?.AuthorKeywords ??
      null;

    if (Array.isArray(akw)) {
      akw.forEach(pushToken);
      return;
    }

    if (typeof akw === "string" && akw.trim()) {
      akw.split(/[,;|]/g).forEach(pushToken);
      return;
    }

    return;
  });

  return Array.from(freq.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, k)
    .map(([key, count]) => ({ key, count }));
}

export function diffKeywords(prevPapers, curPapers, nextPapers, k = 6) {
  const prev = topKeywords(prevPapers, 50);
  const cur = topKeywords(curPapers, 50);
  const next = topKeywords(nextPapers, 50);

  const toMap = (arr) => {
    const m = new Map();
    arr.forEach((x) => m.set(x.key, x.count));
    return m;
  };

  const mp = toMap(prev);
  const mc = toMap(cur);
  const mn = toMap(next);

  const dominant = cur.slice(0, k);

  const emerging = Array.from(mc.entries())
    .map(([key, c]) => {
      const p = mp.get(key) ?? 0;
      const n = mn.get(key) ?? 0;
      const base = (p + n) / 2;
      const delta = Math.round((c - base) * 10) / 10;
      return { key, prev: p, cur: c, next: n, delta };
    })
    .filter((x) => x.cur > x.prev && x.cur > x.next)
    .sort((a, b) => b.delta - a.delta)
    .slice(0, k);

  return { dominant, emerging };
}
