# Play Room v247: lore colours and the 8-minute day (Jordan, 2026-11-22).
#  - "Why do so many maps use purple ... render those areas in colors more fitting to the landscape from the lore"
#    + "keep going with the organic detailed look": the round-2 ground palettes (Dunharrow, Morgul, Isengard,
#    Gorgoroth, Shelob's Lair, Ice Caves, Paths of the Dead, Denethor's balcony, White Mountains) replace the
#    level palettes in the ROM at load. Art is the game's own; only colours change. Built by the recolor tools
#    (project files recolor/tools: plans.py *_O plans, compose.new_palette), data in lore-colors-v247.json.
#  - "give the sky ... morning noon and dusk and add in a night option cycled in two minute intervals slowly fading
#    between them": play time runs morning, noon, dusk, night, 2 minutes each with 1-minute fades (was 4 min day +
#    4 min night). Each outside level's sky palette bank moves between four keyframes (recolor sky.py: FREE lands,
#    SHADOW for Mordor/Isengard, MORGULSKY for the Morgul Vale); the picture look adds a warm morning and a red dusk
#    (torches start to glow at dusk) before the old night. Mordor's fixed look gets a little darker at night.
#    Levels whose ground shares the sky bank (Crack of Doom, Sammath Naur, the Beacons, Fork, Mindolluin, Tower
#    Door) and anything underground keep their sky still.
# Usage: python3 daycycle-v247.py in.html lore-colors-v247.json out.html
import json, sys
p, data, out = sys.argv[1], sys.argv[2], sys.argv[3]; s = open(p, encoding='utf-8').read()
D = json.load(open(data))
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)

lore = json.dumps({'pals': D['pals'], 'sky': D['sky']}, separators=(',', ':'))
rep('        game = g; }\n',
    '        game = g; }\n'
    '      // v247 lore colours (Jordan 2026-11-22): new level palettes for the purple lands, and each outside level\'s sky\n'
    '      // keyframes (bank, own colours, morning/noon/dusk/night as BGR555 hex) for the day cycle below.\n'
    '      window.__LORE = ' + lore + ';\n'
    '      for (const [a, h] of window.__LORE.pals) game.set(hexBytes(h), parseInt(a, 16) - 0x8000000);\n')

# Four times of day on play time.
rep('''    const nightness = () => {
      if (typeof window.__rotkNightForce === "number") return window.__rotkNightForce;
      const T = 480, h = T / 2, r = 30, t = (playT + r / 2) % T, up = (x) => Math.min(1, Math.max(0, x / r));
      let n = t < r / 2 ? 1 - up(t + r / 2) : t < h + r / 2 ? up(t - (h - r / 2)) : 1 - up(t - (T - r / 2));
      return n * n * (3 - 2 * n);
    };
''', '''    // v247: morning, noon, dusk and night, 2 minutes each of play, fading over a minute into the next
    // (Jordan 2026-11-22). Weights for the four, adding up to 1. window.__dayT (seconds) pins the clock for tests.
    const dayT = () => { const t = typeof window.__dayT === "number" ? window.__dayT : playT; return ((t % 480) + 480) % 480; };
    const phaseW = () => {
      if (typeof window.__rotkNightForce === "number") { const k = window.__rotkNightForce; return [0, 1 - k, 0, k]; }
      const p = dayT() / 120, w = [0, 0, 0, 0];
      for (let i = 0; i < 4; i++) { let d = Math.abs(p - (i + 0.5)); d = Math.min(d, 4 - d); const x = Math.min(1, Math.max(0, (0.75 - d) / 0.5)); w[i] = x * x * (3 - 2 * x); }
      return w;
    };
    const nightness = () => phaseW()[3];
    const MORN = { Gain: [1.06, 1.02, 0.94], HiTint: [0.07, 0.045, 0.0], ShadowTint: [0.0, 0.0, 0.045] };
    const DUSK = { Gain: [1.07, 0.93, 0.84], HiTint: [0.09, 0.03, -0.01], ShadowTint: [0.01, -0.01, 0.06], Sat: 1.08, Vig: 0.32, Night: 0.15, NightTint: [0.9, 0.7, 0.72], TorchK: 0.5 };
    const mixW = (parts) => { const o = {}, a = parts[0][0];
      for (const key in a) { if (Array.isArray(a[key])) { const v = [0, 0, 0]; for (const [lk, w] of parts) for (let j = 0; j < 3; j++) v[j] += lk[key][j] * w; o[key] = v; }
        else { let v = 0; for (const [lk, w] of parts) v += lk[key] * w; o[key] = v; } }
      return o; };
    const INSIDE = { 16: 1, 17: 1, 18: 1, 28: 1 };   // Mount Doom's insides: no clock
''')
rep('''      const t = ((typeof window.__sunT === "number" ? window.__sunT : playT) + 15) % 480, day = t < 255, u = day ? Math.min(1, t / 255) : Math.min(1, (t - 240) / 240);
''', '''      const t = typeof window.__sunT === "number" ? ((window.__sunT % 480) + 480) % 480 : dayT(), day = t < 360, u = day ? t / 360 : (t - 360) / 120;   // v247: sun over morning-dusk, moon at night
''')
rep('''      if (FIXED[g]) return Object.assign({}, looks[g], { SunDX: 0.25, SunDY: 0.32, Warm: 0 });
      const k = nightness(); const lk = k <= 0 ? day : blend(day, g === "Helm's Deep" ? looks["Helm's Deep"] : NIGHT, k);
      return Object.assign({}, lk, sunNow(k));
''', '''      const w = phaseW();
      if (FIXED[g]) {
        const f = looks[g], out = !INSIDE[n] && g !== "Caves" && g !== "Dwarf halls";   // v247: outside Mordor is a little darker at dusk and night
        return Object.assign({}, f, out ? { Night: Math.min(0.95, f.Night + 0.1 * w[2] + 0.3 * w[3]) } : {}, { SunDX: 0.25, SunDY: 0.32, Warm: 0 });
      }
      const lk = mixW([[Object.assign({}, day, MORN), w[0]], [day, w[1]], [Object.assign({}, day, DUSK), w[2]], [Object.assign({}, day, g === "Helm's Deep" ? looks["Helm's Deep"] : NIGHT), w[3]]]);
      return Object.assign({}, lk, sunNow(w[3]));
''')
rep('''    return { looks, sunNow, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, names: byLevel, tick, playTime: () => playT, under };
''', '''    return { looks, sunNow, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, phaseW, names: byLevel, tick, playTime: () => playT, under };
''')
# Sky palette writer.
rep('''  // Graphics High/Low (2026-11-12)''', '''  // v247 sky through the day: each outside level's sky colours (its sky palette bank) move between its morning, noon,
  // dusk and night keyframes, written into palette RAM; outside online play also into the game's own palette copy
  // (EWRAM 0x1B090, which screen fades read) so a level fades in with the right sky. Online leaves EWRAM alone (the two
  // pages compare it). Written only while the bank still holds the level's own colours or ours, never during a fade
  // or after the game swaps palettes.
  (() => {
    const dec = (h) => { const o = []; for (let i = 0; i < 15; i++) o.push(parseInt(h.substr(i * 4 + 2, 2) + h.substr(i * 4, 2), 16)); return o; };
    const cache = {}; let last = null, lastLv = -1;
    const get = (lv) => { if (lv in cache) return cache[lv]; const s = window.__LORE.sky[lv];
      return (cache[lv] = s ? { bank: s[0], base: dec(s[1]), keys: s[2].map((h) => dec(h).map((v) => [v & 31, (v >> 5) & 31, (v >> 10) & 31])) } : null); };
    const same = (H, at, a) => { for (let i = 0; i < 15; i++) if ((H[at + i * 2] | (H[at + i * 2 + 1] << 8)) !== a[i]) return false; return true; };
    const eq = (H, x, y) => { for (let i = 0; i < 30; i++) if (H[x + i] !== H[y + i]) return false; return true; };
    const put = (H, at, a) => { for (let i = 0; i < 15; i++) { H[at + i * 2] = a[i] & 255; H[at + i * 2 + 1] = a[i] >> 8; } };
    const step = () => {
      requestAnimationFrame(step);   // every picture, so a level never shows its own sky for a moment before ours
      try {
        const M = window.__wideM; if (!M || !M._rotk_iwram || !M._rotk_ewram || !window.__LORE) return;
        // The shown game: online = this page's player, otherwise game 0. In 2-player engines the palette RAM sits
        // 0x48000 after the game's EWRAM (rotk_pal only knows the 1-player game).
        const mp = window.__mp, link = !!(M._rotk_link_on && M._rotk_link_on()), on = !!(mp && mp.online && mp.ewram);
        const H = M.HEAPU8, b = on ? mp.iwram() : M._rotk_iwram(), ew0 = on ? mp.ewram() : M._rotk_ewram(), st = H[b + 0x41B0], lv = H[b + 0x41F8];
        if (lv !== lastLv) { last = null; lastLv = lv; }
        const s = st === 1 ? get(lv) : null; if (!s) return;
        const w = LIGHT_LOOKS.phaseW(), tgt = [];
        for (let i = 0; i < 15; i++) { let r = 0, g = 0, bl = 0; for (let k = 0; k < 4; k++) { const c = s.keys[k][i]; r += c[0] * w[k]; g += c[1] * w[k]; bl += c[2] * w[k]; }
          tgt.push(Math.round(r) | (Math.round(g) << 5) | (Math.round(bl) << 10)); }
        const pal = (link || !M._rotk_pal ? ew0 + 0x48000 : M._rotk_pal()) + s.bank * 32 + 2;
        const ew = on ? -1 : ew0 + 0x1B090 + s.bank * 32 + 2;
        const ours = (at) => same(H, at, s.base) || (last && same(H, at, last));
        if (ew >= 0 && ours(ew)) { const steady = eq(H, pal, ew); put(H, ew, tgt); if (steady) put(H, pal, tgt); last = tgt; }
        else if (ours(pal)) { put(H, pal, tgt); last = tgt; }
      } catch (e) {}
    };
    requestAnimationFrame(step);
  })();
  // Graphics High/Low (2026-11-12)''')
open(out, 'w', encoding='utf-8').write(s); print('ok v247 day cycle')
