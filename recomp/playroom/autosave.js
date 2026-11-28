// Save on exit (v278, plan Phase 2; Jordan: "auto-save on exit with no save screen (like Diablo 2)"). The game code is
// tools/autosave/autosave.c: when the page sets ASREQ, the next gameplay or Backpack update saves the hero into the
// slot this play session belongs to (the slot the hero was loaded from or last saved to), as the pause menu's Save
// Game does but with no slot screen. The page's own save keeping (this device and the account) then picks the save
// up as it does after any save. The page asks:
//   - when the Backpack opens (the game code itself saves as the pause menu opens, so Quit Game leaves the hero saved),
//   - after every level change (doors, regions, campfire travel), once the new level is playing,
//   - every 3 minutes of play,
//   - when the page is hidden or closed (it then runs a few game ticks itself, since hidden pages get no pictures).
// 1-player only for now: 2-player and online games save each hero in their own game later.
(() => {
  if (window.__autosave) return;
  const ASREQ = 0x0203F3E0, ASDONE = 0x0203F3E1, ASRES = 0x0203F3E2, ASSLOT = 0x0203F3E3, ASON = 0x0203F3E5, DUPELOCK = 0x0203FFF0;
  const EVERY = 180000;
  // 2-player and online games (one engine, link mode) can't run the save code from the state table yet (the link engine
  // stops on it), so their game keeps the game's own gameplay and Backpack updates.
  const linkRom = window.__linkRom;
  if (linkRom) window.__linkRom = (r) => {
    const o = linkRom(r);
    const w = (at, v) => { o[at] = v & 255; o[at + 1] = (v >>> 8) & 255; o[at + 2] = (v >>> 16) & 255; o[at + 3] = v >>> 24; };
    if (o[0x6C838] === 0x01 && o[0x6C839] === 0x30 && o[0x6C83A] === 0x09) { w(0x6C838, 0x08031E45); w(0x6C8A4, 0x0802A799); }
    return o;
  };
  const st = { asked: 0, done: 0, last: null, why: "", at: 0 };
  window.__autosave = st;
  const mem = () => {
    const mp = window.__mp, M = mp && mp.M; if (!M || !M.HEAPU8 || mp.online) return null;
    if (M._rotk_link_on && M._rotk_link_on()) return null;
    let iw = -1, ew = -1;
    try { iw = mp.iwram(); ew = mp.ewram ? mp.ewram() : M._rotk_ewram ? M._rotk_ewram() : -1; } catch (e) { return null; }
    if (!(iw > 0) || !(ew > 0)) return null;
    const H = M.HEAPU8, E = (a) => ew + (a & 0x3ffff);
    return { M, H, E, iw, st: H[iw + 0x41B0], lv: H[iw + 0x4174] };
  };
  // only once the game has the save code in (the Modded game; an older page ROM leaves these bytes alone)
  const ready = () => { try { const g = window.__romFull; return !!(g && g[0x6C838] === 0x01 && g[0x6C839] === 0x30 && g[0x6C83A] === 0x09 && g[0x6C83B] === 0x08); } catch (e) { return false; } };
  const ask = (why) => {
    const m = mem(); if (!m || !ready()) return false;
    if (!m.H[m.E(DUPELOCK)]) return false;     // a new game that was never saved has no slot yet
    m.H[m.E(ASREQ)] = 1; st.asked++; st.why = why; st.at = Date.now();
    return true;
  };
  let lastAsked = 0, seenDone = -1, lastSt = -1, lastLv = -1, lvWait = 0, playSince = 0;
  const watch = () => {
    const m = mem();
    if (m) {
      if (ready()) m.H[m.E(ASON)] = 1;   // the game's own save as the pause menu opens (2-player games never get this)
      const d = m.H[m.E(ASDONE)];
      if (seenDone >= 0 && d !== seenDone) { st.done++; st.last = { res: m.H[m.E(ASRES)], slot: m.H[m.E(ASSLOT)], why: st.asked !== lastAsked ? st.why : "pause", at: Date.now() }; lastAsked = st.asked; }
      seenDone = d;
      if (m.st === 10 && lastSt !== 10) ask("backpack");
      if (m.st === 1) {
        if (lastLv >= 0 && m.lv !== lastLv) lvWait = performance.now() + 1500;
        if (lvWait && performance.now() > lvWait) { lvWait = 0; ask("level " + m.lv); }
        if (!playSince) playSince = performance.now();
        else if (performance.now() - playSince > EVERY) { playSince = performance.now(); ask("timer"); }
        lastLv = m.lv;
      }
      lastSt = m.st;
    }
    setTimeout(watch, 250);
  };
  setTimeout(watch, 1000);
  // The engine writes the save chip to its file a few seconds after the game writes it, which is too late for a page
  // that is closing. So on leaving, the page puts the blocks the save just wrote into a copy of the file itself, from
  // the same memory the game wrote them from (tools/orcslots save_wrap: EEPROM blocks are 8 bytes, stored reversed):
  // the file header (blocks 0-7), the slot (page 1: blocks 8 + 14 slot; page 2: 65 + 14 slot and its heads 121 + slot),
  // its arrow slots (125 + 4 page + slot) and stash (133 + 3 (4 page + slot)).
  const withSave = (m, file, pg, slot) => {
    const b = file.slice(), I = (a) => m.iw + (a & 0x7fff);
    const put = (block, src, n) => { for (let k = 0; k < n; k++) for (let i = 0; i < 8; i++) b[8 * (block + k) + i] = m.H[src + 8 * k + 7 - i]; };
    put(0, I(0x030057F0), 8);
    if (!pg) put(8 + 14 * slot, I(0x03005630 + 0x70 * slot), 14);
    else { put(65 + 14 * slot, m.E(0x0203F010 + 0x70 * slot), 14); put(121 + slot, m.E(0x0203F1D0 + 8 * slot), 1); }
    if (m.H[m.E(0x0203F314)] === 1) { const k = 4 * pg + slot; put(125 + k, m.E(0x0203F2D0 + 8 * k), 1); put(133 + 3 * k, m.E(0x0203F8D0 + 24 * k), 3); }
    return b;
  };
  st.withSave = withSave;
  const fileNow = (m) => { try { return m.M.FS.readFile("/data/saves/rotk-modded.sav"); } catch (e) { return null; } };
  const b64 = (b) => { let t = ""; for (let i = 0; i < b.length; i += 0x8000) t += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); return btoa(t); };
  // hidden or closing: ask, run the game for a few ticks so the save happens now, and keep the saved file on this device
  const leave = () => {
    const m = mem(); if (!m) return;
    if (m.st === 1 || m.st === 10) {
      if (ask("leave")) { const d0 = m.H[m.E(ASDONE)]; for (let i = 0; i < 6 && m.H[m.E(ASDONE)] === d0; i++) { try { m.M._rotk_bg_tick(); } catch (e) { break; } } }
    } else if (m.st !== 16) return;   // the pause menu: the game saved as it opened
    if (m.H[m.E(ASRES)] !== 1 || !m.H[m.E(ASDONE)]) return;   // nothing saved this session
    const f = fileNow(m); if (!f || f.length !== 8192) return;
    const at = m.H[m.E(ASSLOT)], b = withSave(m, f, (at >> 4) & 1, at & 3);
    try { localStorage.setItem("rotk-wide-sav", JSON.stringify({ data: b64(b), at: Date.now() })); st.kept = Date.now(); } catch (e) {}
  };
  window.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") leave(); }, true);   // capture: before the page's save keeping
  window.addEventListener("pagehide", leave, true);
  st.ask = ask; st.mem = mem; st.fileNow = fileNow;
})();
