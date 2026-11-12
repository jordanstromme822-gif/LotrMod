#!/usr/bin/env python3
"""Play Room: P2 keeps your hero when it is on save page 2 (2026-11-12).

  python3 p2-pages-v170.py in.html out.html

Jordan: "Stop switching my character when I load a P2 from the original I selected". The game has 4 save slots; the
second page of slots (tools/orcslots) swaps page-2 heroes into them. The P2 button only passed the slot number
(0x03005834), and the 2-player start always picked that slot on page 1, so a page-2 hero (say Gandalf on page 2,
slot 2) came back as whoever sits in slot 2 of page 1. Now the page of your hero (SESSPG 0x0203F007, valid while
SESSV 0x0203F009) goes along as p1pg, the P2 list also offers page-2 heroes (p2pg), and the 2-player start turns
each game's Load Game screen to the right page (R, like the Page button) before it picks the slots.
"""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)

# Saved heroes of either page: page 1 at 0x40 + 0x70 k; page 2 (8 KB save chip, v124) at block 65 = byte 520, only when
# the save file has the LOTRXT01 marker (block 64, stored with its bytes reversed).
rep('''  const p2SlotInfo = (b) => {
    const out = [];
    for (let k = 0; k < 4; k++) {
      const o = 0x40 + k * 0x70; let used = false;''',
'''  const p2HasPage2 = (b) => { if (!b || b.length < 0x200 + 0x40 + 4 * 0x70) return false; const m = String.fromCharCode(...b.slice(512, 520)); return m === "10TXRTOL" || m === "LOTRXT01"; };
  const p2SlotInfo = (b, pg) => {
    const out = [];
    if (pg && !p2HasPage2(b)) return [null, null, null, null];
    for (let k = 0; k < 4; k++) {
      const o = (pg ? 520 : 0x40) + k * 0x70; let used = false;''')
rep('''return j && j.p2 >= 0 && j.p2 < 4 && j.p1 >= 0 && j.p1 < 4 && j.p1 !== j.p2 ? j : null;''',
    '''return j && j.p2 >= 0 && j.p2 < 4 && j.p1 >= 0 && j.p1 < 4 && (j.p1 !== j.p2 || (j.p1pg | 0) !== (j.p2pg | 0)) ? j : null;''')
rep('''if (link) { const info = p2SlotInfo(save); if (!info[link.p1] || !info[link.p2]) {''',
    '''if (link) { if (!p2SlotInfo(save, link.p1pg | 0)[link.p1] || !p2SlotInfo(save, link.p2pg | 0)[link.p2]) {''')
rep('''if (cfg.p1 === cfg.p2 || cfg.p1 > 3) {''', '''if ((cfg.p1 === cfg.p2 && (cfg.p1pg | 0) === (cfg.p2pg | 0)) || cfg.p1 > 3) {''')
rep('''const s = p2SlotInfo(save)[link.p2];''', '''const s = p2SlotInfo(save, link.p2pg | 0)[link.p2];''')
rep('''      const m = mem(0), cur = m.ok ? m.r8(0x03005834) : -1, lvl = playLvl || (m.ok ? m.r8(0x030041F8) : 0);
      const list = p2SlotInfo(readSave() || save).filter((s) => s && s.slot !== cur);''',
'''      // Your hero's save page (v170): SESSPG 0x0203F007 while SESSV 0x0203F009 is set (tools/orcslots).
      const m = mem(0), cur = m.ok ? m.r8(0x03005834) : -1, curPg = m.ok && m.r8(0x0203F009) ? m.r8(0x0203F007) & 1 : 0, lvl = playLvl || (m.ok ? m.r8(0x030041F8) : 0);
      const sv = readSave() || save;
      const list = [0, 1].flatMap((pg) => p2SlotInfo(sv, pg).map((s) => s && Object.assign(s, { pg }))).filter((s) => s && !(s.slot === cur && s.pg === curPg));''')
rep('''      for (const s of list) add((P2_HEROES[s.hero] || "Hero") + " · level " + s.level, () => {
        close(); doJoin({ p1: cur, p2: s.slot, moria: lvl === 82, level: lvl });''',
'''      for (const s of list) add((P2_HEROES[s.hero] || "Hero") + " · level " + s.level + (s.pg ? " · page 2" : ""), () => {
        close(); doJoin({ p1: cur, p1pg: curPg, p2: s.slot, p2pg: s.pg, moria: lvl === 82, level: lvl });''')
rep('''doJoin({ p1: link.p1, p2: link.p2, moria: lv === 82, level: lv });''',
    '''doJoin({ p1: link.p1, p1pg: link.p1pg | 0, p2: link.p2, p2pg: link.p2pg | 0, moria: lv === 82, level: lv });''')
# Load Game: turn each game to its hero's page first (R flips the slot page, as the Page button does).
rep('''        const want = [link.p1, link.p2], c = [cursor(0), cursor(1)];
        if (c[0] === want[0] && c[1] === want[1]) {''',
'''        const wantPg = [link.p1pg | 0, link.p2pg | 0], pg = [mem(0).r8(0x0203F000) & 1, mem(1).r8(0x0203F000) & 1];
        if (pg[0] !== wantPg[0] || pg[1] !== wantPg[1]) {
          if (++boot.tries > 12) { fail("couldn't turn to the right save page"); return; }
          press(pg[0] !== wantPg[0] ? K.R : 0, pg[1] !== wantPg[1] ? K.R : 0, 4, 40); return;
        }
        const want = [link.p1, link.p2], c = [cursor(0), cursor(1)];
        if (c[0] === want[0] && c[1] === want[1]) {''')
rep('''if (cursor(0) === link.p1 && cursor(1) === link.p2) press(K.A, K.A, 6, 60);''',
    '''if (cursor(0) === link.p1 && cursor(1) === link.p2 && (mem(0).r8(0x0203F000) & 1) === (link.p1pg | 0) && (mem(1).r8(0x0203F000) & 1) === (link.p2pg | 0)) press(K.A, K.A, 6, 60);''')
rep('''slog("boot done, P1 slot " + link.p1 + ", P2 slot " + link.p2 + ", level "''',
    '''slog("boot done, P1 slot " + link.p1 + (link.p1pg ? " (page 2)" : "") + ", P2 slot " + link.p2 + (link.p2pg ? " (page 2)" : "") + ", level "''')
open(dst, "w", encoding="utf-8").write(s)
print("ok")
