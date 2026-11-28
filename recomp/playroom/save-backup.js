// Save backups (v277, plan Phase 2 "save migration before save-on-exit"). Save on exit will write each hero's slot
// without a save screen, so a hero kept by saving into a second slot, or a slot saved over by mistake, can't be
// undone from the game any more. Before that comes in, the page keeps copies of every saved-games doc on the
// player's account:
//   data/users/<id>/save-backup-first    the first copy this page ever made (written once, never replaced)
//   data/users/<id>/save-backup-<0..2>   one a day, the oldest of the three replaced
// Each copy holds the four docs the saves are kept in (save-rotk-modded, -page2, -arrows, campfires) as they are on
// the account, and the device's own copies (localStorage) when the account has none. Restoring is done by hand from
// a copy (Claude, through the account database), so nothing here ever writes the saved-games docs themselves.
(() => {
  if (window.__saveBackup) return;
  const DOCS = ["save-rotk-modded", "save-rotk-modded-page2", "save-rotk-modded-arrows", "campfires"];
  const LOCAL = { "save-rotk-modded": "rotk-wide-sav", "save-rotk-modded-page2": "rotk-page2", "save-rotk-modded-arrows": "rotk-arrows", "campfires": "rotk-campfires" };
  const DAY = 86400000, KEEP = 3;
  const state = { done: false, wrote: [], err: null };
  window.__saveBackup = state;
  const timeout = (p, ms) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error("timeout")), ms))]);
  const run = async () => {
    const [db, user] = await Promise.all([window.claude?.use?.("db"), window.claude?.use?.("user")]);
    const id = db && user ? await user.id() : null;
    if (!id) { state.done = true; return; }
    const base = "data/users/" + id + "/";
    const copy = { at: Date.now(), docs: {} };
    for (const n of DOCS) {
      let d = null;
      try { const s = await timeout(db.doc(base + n).get(), 15000); d = s && s.exists ? s.data() : null; } catch (e) { state.err = "read " + n; return; }
      if (!d) { try { const j = JSON.parse(localStorage.getItem(LOCAL[n]) || "null"); if (j) d = Object.assign({ device: true }, j); } catch (e) {} }
      if (d) copy.docs[n] = d;
    }
    if (!copy.docs["save-rotk-modded"]) { state.done = true; return; }   // no saved games yet: nothing to keep
    const get = async (n) => { try { const s = await timeout(db.doc(base + n).get(), 15000); return s && s.exists ? s.data() : null; } catch (e) { return undefined; } };
    const first = await get("save-backup-first");
    if (first === null) { await db.doc(base + "save-backup-first").set(copy); state.wrote.push("first"); }
    const ring = [];
    for (let i = 0; i < KEEP; i++) ring.push(await get("save-backup-" + i));
    if (ring.some((r) => r === undefined)) { state.err = "read ring"; state.done = true; return; }   // never overwrite a copy we couldn't read
    const newest = Math.max(0, ...ring.map((r) => (r && r.at) || 0));
    if (Date.now() - newest >= DAY) {
      let slot = 0; for (let i = 1; i < KEEP; i++) if (((ring[i] && ring[i].at) || 0) < ((ring[slot] && ring[slot].at) || 0)) slot = i;
      await db.doc(base + "save-backup-" + slot).set(copy); state.wrote.push(slot);
    }
    state.done = true;
  };
  // after the page has loaded the saves (a page that only opened shouldn't hold up the game's own loading)
  setTimeout(() => run().catch((e) => { state.err = String(e && e.message || e); state.done = true; }), 20000);
})();
