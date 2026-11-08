// Phone version of the Play Room (Jordan, 2026-11-08: play full screen from the Home Screen, without the Claude bar).
// Stands in for the Claude account features the Play Room uses: saves and the game file live on this phone
// (IndexedDB); the engine and game come from the game pack the player picked once (served by sw.js).
(() => {
  const DB = "rotk-phone", ST = "kv";
  let dbP = null;
  const idb = () => dbP || (dbP = new Promise((res, rej) => {
    const o = indexedDB.open(DB, 1);
    o.onupgradeneeded = () => o.result.createObjectStore(ST);
    o.onsuccess = () => res(o.result); o.onerror = () => rej(o.error);
  }));
  const kvGet = async (k) => { const d = await idb(); return new Promise((r) => { const q = d.transaction(ST).objectStore(ST).get(k); q.onsuccess = () => r(q.result); q.onerror = () => r(undefined); }); };
  const kvSet = async (k, v) => { const d = await idb(); return new Promise((r, j) => { const t = d.transaction(ST, "readwrite"); t.objectStore(ST).put(v, k); t.oncomplete = () => r(); t.onerror = () => j(t.error); }); };
  window.__phoneKv = { get: kvGet, set: kvSet };
  try { navigator.storage && navigator.storage.persist && navigator.storage.persist(); } catch (e) {}
  const norm = (p) => p.replace(/^data\/users\/[^/]+\//, "data/users/me/");
  const db = { doc: (path) => ({
    get: async () => { const v = await kvGet(norm(path)); return { exists: v !== undefined, data: () => v }; },
    set: async (v) => { await kvSet(norm(path), JSON.parse(JSON.stringify(v))); },
  }) };
  const share = async (blob, name) => {
    const f = new File([blob], name, { type: blob.type || "application/octet-stream" });
    try { if (navigator.canShare && navigator.canShare({ files: [f] })) { await navigator.share({ files: [f] }); return; } } catch (e) { if (e && e.name === "AbortError") return; }
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 60000);
  };
  const downloads = { save: async (o) => share(o.data, o.filename || o.name || "rotk-file") };
  const user = { id: async () => "me", isOwner: () => true, profiles: async () => ({}) };
  // No "room": online games need the Claude Play Room (P2 still works here).
  window.claude = { use: async (n) => n === "db" ? db : n === "user" ? user : n === "downloads" ? downloads : null };

  // Saves backup / restore (a file the player keeps in Files or iCloud).
  const SAVE = "data/users/me/save-rotk-modded";
  const backup = async () => {
    const v = await kvGet(SAVE); if (!v) { alert("No saved games on this phone yet."); return; }
    const d = new Date(), stamp = d.getFullYear() + String(d.getMonth() + 1).padStart(2, "0") + String(d.getDate()).padStart(2, "0") + "-" + String(d.getHours()).padStart(2, "0") + String(d.getMinutes()).padStart(2, "0");
    await share(new Blob([JSON.stringify({ rotkSaves: 1, ...v })], { type: "application/json" }), "rotk-saves-" + stamp + ".json");
  };
  const restore = (file) => file.text().then(async (t) => {
    let v; try { v = JSON.parse(t); } catch (e) { v = null; }
    if (!v || typeof v.data !== "string") { alert("That file isn't a saves backup."); return; }
    if (!confirm("Replace the saved games on this phone with this backup?")) return;
    const old = await kvGet(SAVE); if (old) await kvSet("data/users/me/save-before-restore", old);
    await kvSet(SAVE, { at: Date.now(), data: v.data, size: v.size || 512 });
    try { for (const k of Object.keys(localStorage)) if (/save/i.test(k) && /rotk/i.test(k)) localStorage.removeItem(k); } catch (e) {}
    location.reload();
  });
  document.addEventListener("DOMContentLoaded", () => {
    const play = document.getElementById("play"); if (!play) return;
    const box = document.createElement("div");
    box.style.cssText = "margin:10px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center";
    box.innerHTML = '<button type="button" class="btn pill" id="phBackup">Back up saves</button><button type="button" class="btn pill" id="phRestore">Restore saves</button><input type="file" id="phFile" accept=".json,application/json" hidden><span style="font-size:12px;opacity:.7">Phone version: saves stay on this phone. Back them up now and then.</span>';
    play.insertAdjacentElement("afterend", box);
    document.getElementById("phBackup").onclick = backup;
    document.getElementById("phRestore").onclick = () => document.getElementById("phFile").click();
    document.getElementById("phFile").onchange = (e) => { const f = e.target.files[0]; if (f) restore(f); e.target.value = ""; };
  });
})();
