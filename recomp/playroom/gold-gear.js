  // v213 Gold border on better gear (Jordan, 2026-11-20: "items in your inventory that have a higher item level
  // (character requirement level) or higher current stats than the item you have currently equipped that that item
  // would slot into should have a gold border in the inventory screen and forge screen").
  // window.__goldGear(item, worn, heroId): true when `item` is gear this hero can wear and it beats what they wear in
  // that slot: a higher Min. Level (the game's own sum, 0x0802D2F8) or more stat points (prefix + base + suffix, Cheap and
  // Cursed count against it), or the slot is empty. worn = the hero's 8 worn item words (hero + 0x3C, order: armor,
  // weapon, shield, helmet, cape, gloves, footwear, amulet; the item's slot is bits 18-25 of its list word). Arrows,
  // Orc Heads and other unique items are never marked. The HD Backpack and the HD Forge / Shrine call it for their boxes
  // (and the Forge's gear for sale) and add a gold border with a small arrow. Page only, so 1-player, P2 and online alike.
  window.__goldGear = (() => {
    const CNT = [18, 11, 9, 11, 10, 4, 13, 10, 24, 8, 12, 9, 8, 7];
    const R = () => window.__romFull;
    const U8 = (o) => R()[o];
    const U32 = (o) => { const r = R(); return (r[o] | r[o + 1] << 8 | r[o + 2] << 16 | r[o + 3] << 24) >>> 0; };
    const S8 = (v) => (v > 127 ? v - 256 : v);
    const TXT = {};
    const text = (id) => {   // tools/text.py
      if (id in TXT) return TXT[id];
      const r = R(), bank = U32(0x289A10) - 0x08000000, tree = bank + 4, table = tree + U32(bank);
      let p = bank + U32(table + 4 * id), node = 0x100, bit = 0, byte = r[p++], s = "";
      for (let n = 0; n < 300; n++) {
        while (node > 0xFF) { const e = tree + (node - 0x100) * 4; node = (r[(byte >> bit) & 1 ? e + 2 : e] | r[((byte >> bit) & 1 ? e + 2 : e) + 1] << 8); if (++bit === 8) { bit = 0; byte = r[p++]; } }
        if (!node) break;
        s += String.fromCharCode(node); node = 0x100;
      }
      return (TXT[id] = s);
    };
    const catw = (c, k) => U32(0x68F50 + c * 0x28 + 4 * k) - 0x08000000;
    const flags = (c, i) => U32(catw(c, 8) + 8 * i);
    const split = (it) => ({ c: it & 15, i: (it >>> 8) & 255, pre: (it >>> 16) & 255, suf: it >>> 24 });
    const gear = (it) => { if (it === 0 || it === 0xFFFFFFFF) return false; const { c, i } = split(it); return c < 14 && c !== 7 && i < CNT[c]; };
    const ents = (it) => {
      const { c, i, pre, suf } = split(it), o = [catw(c, 0) + 12 * i];
      if (pre !== 255) o.push(catw(c, 2) + 12 * pre);
      if (suf !== 255) o.push(catw(c, 5) + 12 * suf);
      return o;
    };
    const level = (it) => {
      const { c, i, pre, suf } = split(it), f = flags(c, i);
      let r = U8(catw(c, 0) + 12 * i + 2);
      if (f & 0x80) r += 5; if (f & 0x100) r += 5;
      if (pre !== 255) { r += U8(catw(c, 2) + 12 * pre + 2) >> 1; const pf = U32(catw(c, 3) + 4 * pre); r += 5 * !!(pf & 1) + 5 * !!(pf & 2); }
      if (suf !== 255) { r += U8(catw(c, 5) + 12 * suf + 2); const sf = U32(catw(c, 6) + 4 * suf); r += 5 * !!(sf & 1) + 5 * !!(sf & 2); }
      if (f & 0x10000) r = 1;
      return r & 255;
    };
    const score = (it) => {
      let v = 0;
      for (const e of ents(it)) for (let k = 3; k < 11; k += 2) {
        const s = U8(e + k); if (s === 0x5a) continue;
        const nm = text(329 + s);
        v += nm === "Cursed" ? -50 : nm === "Cheap" ? -5 : S8(U8(e + k + 1));
      }
      return v;
    };
    const slot = (it) => { const { c, i } = split(it), m = flags(c, i); for (let b = 0; b < 8; b++) if (m & (1 << (18 + b))) return b; return -1; };
    const memo = new Map();
    const better = (it, worn, heroId) => {
      it >>>= 0;
      if (!R() || !gear(it) || !worn) return false;
      const { c, i } = split(it), f = flags(c, i);
      if (f & 0x10000) return false;                                    // backpack-only items
      if (heroId < 6 && !(f & (1 << (26 + heroId)))) return false;      // not gear this hero can wear
      const s = slot(it); if (s < 0) return false;
      const w = worn[s] >>> 0;
      if (w === it) return false;
      if (!gear(w) || slot(w) !== s) return true;                       // nothing worn there
      const key = it + ":" + w; let r = memo.get(key);
      if (r === undefined) { r = level(it) > level(w) || score(it) > score(w); if (memo.size > 4000) memo.clear(); memo.set(key, r); }
      return r;
    };
    better.level = level; better.score = score; better.slot = slot;
    return better;
  })();
