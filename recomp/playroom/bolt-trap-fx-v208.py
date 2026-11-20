#!/usr/bin/env python3
"""Play Room v208 (Jordan, 2026-11-20): Frodo's Bolt Trap aims smoothly, and its arrows matter.

  bolt-trap-fx-v208.py in.html out.html

Apply on a page that has v202 + v203 (bolt-trap-v202.py, bolt-trap-crouch-v203.py).

- 32 facings ("Give the trap turn 32 steps of animation"): tools/xbbig/xbart.py with FACINGS=32 draws the bronze
  ballista every 11.25 degrees (xb32.bin, 16 KB at ROM 0x95000-0x99000, freed Italian text bank) with a 32-frame
  record list at ROM 0x99000; crossbow.c's xb_anim (orcslots, 0x080852D0) points at it. Frames 0-7 are the 8 main
  ways, which crossbow.c's own fire() still picks, so nothing in the compiled game code changes.
- Smooth aiming: every game tick the page turns each crossbow one facing (of 32) toward the foe its code will shoot
  (the same pick as crossbow.c nearest(): the closest live foe within 120 x 80 px), by writing its frame (+0x23).
  The game's angle for a bolt is also 32 steps, so a bolt leaves along the way the ballista points.
- Elven Arrows (arrow type 5, text 674) in Frodo's arrow slot: each shot is a burst of 3 bolts, 2 game ticks apart.
  After the game's own shot the page sets the reload counter (list entry + 7) to 2 twice and adds 2 to the shots left
  (+6) and 2 to the arrow count, so a burst still costs one arrow and one of the trap's 10 shots.
- Fire Arrows (type 6, text 675): the loaded bolt burns on the ballista (flame + embers on the tip on the effects layer,
  and the tip light turns orange in the lighting pass), and a fire bolt bursts into a small explosion (flash, ring,
  embers, smoke, a little shake) where it hits. Looks only: the damage is the arrows' own.
Writes go through btWrite like v202 (online: they travel with the buttons; one-game P2: both players).
"""
import json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
art = open(os.path.join(ROOT, "tools", "xbbig", "xb32.bin"), "rb").read()
meta = json.load(open(os.path.join(ROOT, "tools", "xbbig", "xb32.json")))
assert len(art) == 16384 and len(meta["tip"]) == 32

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:90]!r}")
    s = s.replace(old, new)

# ---- ROM: 32 pictures + a 32-record frame list ----
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x95000\); // v203: [^\n]*',
               lambda m: 'game.set(hexBytes("%s"), 0x95000); // v208: crossbow trap, bronze ballista, 32 facings (tools/xbbig/xbart.py FACINGS=32)\n'
                         '      game.set(hexBytes("%%s"), 0x99000); // v208: its 32 frame records' % art.hex(), s)
assert k == 1
m = re.search(r'game\.set\(hexBytes\("([0-9a-f]+)"\), 0x9F000\);', s)
t16 = bytes.fromhex(m.group(1))
FR = 0x9B8                                     # turn16 xb16_frames (16 records after v202's 32x32 change)
assert t16[FR + 6] == 0x10 and struct.unpack_from("<H", t16, FR + 8)[0] == 0x200
fl = bytearray(t16[FR:FR + 12]); fl[6] = 32
for n in range(32): fl += struct.pack("<H", 0x40 + 0x12 * n)
rec0 = t16[FR + 0x2C:FR + 0x2C + 0x12]
assert rec0[2] == 0x20 and rec0[3] == 0x20
for n in range(32):
    r = bytearray(rec0); struct.pack_into("<HH", r, 4, n * 0x200, 0x200); fl += r
s = s.replace('game.set(hexBytes("%s"), 0x99000)', 'game.set(hexBytes("%s"), 0x99000)' % fl.hex(), 1)
m = re.search(r'game\.set\(hexBytes\("([0-9a-f]+)"\), 0x7F000\);', s)
orc = bytearray(bytes.fromhex(m.group(1)))
XA = 0x852D0 - 0x7F000
assert struct.unpack_from("<II", orc, XA) == (0x08095000, 0x0809F9B8), "xb_anim not as v202 left it"
struct.pack_into("<II", orc, XA, 0x08095000, 0x08099000)
s = s[:m.start(1)] + orc.hex() + s[m.end(1):]

# ---- glow: 32 facings, orange tip for fire arrows ----
s, k = re.subn(r"const XB_TIP = \[.*?\], XB_BOW = \[.*?\];[^\n]*\n",
               lambda m: "const XB_TIP = %s, XB_BOW = %s;   // v208: 32 facings (tools/xbbig/xb32.json); bow = string end, nock, string end\n"
                         "  window.__XB_TIP = XB_TIP;\n" % (json.dumps(meta["tip"]), json.dumps(meta["bow"])), s, flags=re.S)
assert k == 1
rep("        const f = H8[o + 0x22] & 15, x0 = dv.getInt16(o + 0xAE, true)", "        const f = H8[o + 0x22] & 31, x0 = dv.getInt16(o + 0xAE, true)")
rep("        out.push([x0 + t[0], y0 + t[1], x0 + b[0], y0 + b[1], x0 + b[4], y0 + b[5], x0 + b[2], y0 + b[3]]);",
    "        const aw = dv.getUint32(eb + 0x3F2A0 + 8 * p, true), fire = (aw & 15) === 7 && ((aw >>> 8) & 255) === 6 && ((aw >>> 16) & 255) > 0;   // v208: Fire Arrows loaded\n"
    "        out.push([x0 + t[0], y0 + t[1], x0 + b[0], y0 + b[1], x0 + b[4], y0 + b[5], x0 + b[2], y0 + b[3], fire ? 2 : 1]);")
rep("trapTU.set([(q[0] - sx) / w, (q[1] - sy) / h, 1, 1], 4 * i);", "trapTU.set([(q[0] - sx) / w, (q[1] - sy) / h, q[8] || 1, 1], 4 * i);")
rep("if (TrapT[i].z < 0.001) continue;\\n", "if (TrapT[i].z < 0.001) continue;\\n    float fz = step(1.5, TrapT[i].z);\\n", 2)
rep("vec3 tg = vec3(0.92, 0.97, 1.0) * tc + vec3(0.42, 0.68, 1.0) * th;\\n",
    "vec3 tg = mix(vec3(0.92, 0.97, 1.0) * tc + vec3(0.42, 0.68, 1.0) * th, vec3(1.0, 0.85, 0.5) * tc * (0.8 + 0.4 * sin(Time * 17.0 + float(i))) + vec3(1.0, 0.42, 0.08) * th * 1.5, fz);\\n", 2)
rep("tg * TrapT[i].z, 0.0, 1.0));\\n  }\\n", "tg * min(TrapT[i].z, 1.0), 0.0, 1.0));\\n  }\\n", 2)

# ---- effects layer: a flame tongue particle (k 4) ----
rep("        } else if (p.k === 3) {   // wisp",
    "        } else if (p.k === 4) {   // v208 flame tongue: a tall flickering glow that shrinks as it rises\n"
    "          const fl = 0.7 + 0.3 * Math.sin(p.t * 40 + p.ph), rw = 2.6 * p.w * k * (1 - f * 0.6), rh = rw * 1.9;\n"
    "          x.globalAlpha = (1 - f) * fl; x.drawImage(glow(col), px - rw, py - rh, rw * 2, rh * 2); x.globalAlpha = 1;\n"
    "        } else if (p.k === 3) {   // wisp")

# ---- aiming + elven bursts (game side), in the Bolt Trap scope ----
A = s.index("        window.__bPick = (any, range) => {")
AIM = r'''        // v208 (Jordan, 2026-11-20): the trap turns smoothly in 32 steps toward the foe it will shoot (crossbow.c nearest():
        // closest live foe within 120 x 80 px), one step a game tick, by writing its frame (+0x23; frame k shows facing
        // XB_ORDER[k]). Elven Arrows (type 5) in the arrow slot: every shot is a burst of 3 bolts 2 ticks apart; the page
        // gives back the 2 extra arrows and shots, so a burst costs one of each.
        const XB_ORDER = [0, 4, 8, 12, 16, 20, 24, 28, 2, 6, 10, 14, 18, 22, 26, 30, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31];
        const XB_FRAME = []; XB_ORDER.forEach((f, k) => { XB_FRAME[f] = k; });
        const xbS = new Map(), xbW = [0xFFFFFFFF, 0xFFFFFFFF];
        let xbTick = -1;
        const xbFoe = (o) => {
          const ox = r16s(o + 0xAE), oy = r16s(o + 0xB2); let bd = 1e9, best = null;
          for (let e = r32(0x03002420), n = 0; e >>> 24 === 2 && n < 200; e = r32(e), n++) {
            const f = r32(e + 0xE8) >>> 0;
            if ((f & 0x801000) !== 0x1000 || !(f & 0x10040400)) continue;
            const st = r8(e + 0x62);
            if (st === 0x11 || st === 0x15 || st === 4 || (r8(e + 0x69) & 0x40)) continue;
            const dx = r16s(e + 0xAE) - ox, dy = r16s(e + 0xB2) - oy;
            if (dx < -120 || dx > 120 || dy < -80 || dy > 80) continue;
            const d = dx * dx + dy * dy; if (d < bd) { bd = d; best = [dx, dy]; }
          }
          return best;
        };
        const r16s = (a) => { const v = r8(a) | (r8(a + 1) << 8); return v > 32767 ? v - 65536 : v; };
        const isArrow = (w, t) => (w & 15) === 7 && ((w >>> 8) & 255) === t;
        setInterval(() => {
          try {
            if (iwram < 0 || (window.__mp && window.__mp.online && !window.__mp.sync)) return;
            ew = findEw(); H8 = heap(); if (ew < 0) return;
            const now = btNow(); if (now === xbTick) return;
            const steps = xbTick < 0 ? 1 : Math.max(1, Math.min(4, (now - xbTick) | 0)); xbTick = now;
            const me = r8(0x03003F59) & 1, live = new Set();
            for (const pl of btOne() ? [0, 1] : [me]) {
              const n = Math.min(3, r8(0x0203F390 + pl)), aw = r32(0x0203F2A0 + 8 * pl) >>> 0;
              for (let k = 0; k < n; k++) {
                const e = 0x0203F360 + pl * 24 + k * 8, o = r32(e);
                if (o >>> 24 !== 2 || r8(o + 0x62) === 4 || (r32(o + 0x14) >>> 0) !== 0x08083105 || (r32(o + 0x24) >>> 0) !== 0x080852D0) continue;
                live.add(o);
                let q = xbS.get(o), sh = r8(e + 6);
                if (!q) { q = { f: XB_ORDER[r8(o + 0x23) & 31], shots: sh, vol: 0 }; xbS.set(o, q); }
                if (sh < q.shots) {   // the game just shot
                  if (q.vol > 0) { if (--q.vol > 0) btWrite(e + 7, 2); }
                  else {
                    const pw = xbW[pl] >>> 0;
                    if (sh > 0 && isArrow(pw, 5)) {   // Elven Arrows: 2 more bolts, arrows and shots given back
                      const c = isArrow(aw, 5) ? (aw >>> 16) & 255 : 0, nw = ((pw & 0xFF00FFFF) | (Math.min(255, c + 2) << 16)) >>> 0;
                      for (let i = 0; i < 4; i++) btWrite(0x0203F2A0 + 8 * pl + i, (nw >>> (8 * i)) & 255);
                      sh = Math.min(255, sh + 2); btWrite(e + 6, sh); btWrite(e + 7, 2); q.vol = 2;
                    }
                  }
                }
                q.shots = sh;
                const t = xbFoe(o);
                if (t) {
                  const want = Math.round(Math.atan2(t[0], -(t[1] + 4)) / (2 * Math.PI) * 32) & 31;
                  let d = ((want - q.f + 48) & 31) - 16;
                  q.f = (q.f + Math.sign(d) * Math.min(Math.abs(d), steps) + 32) & 31;
                }
                const fr = XB_FRAME[q.f];
                if (r8(o + 0x23) !== fr) btWrite(o + 0x23, fr);
              }
              xbW[pl] = r32(0x0203F2A0 + 8 * pl) >>> 0;
            }
            for (const o of xbS.keys()) if (!live.has(o)) xbS.delete(o);
          } catch (e) {}
        }, 8);
'''
s = s[:A] + AIM + s[A:]

# ---- fire arrows: burning tip + explosion on hit (effects layer, looks only) ----
FIRE = r'''
<script>
// v208 Fire Arrows on Frodo's Bolt Trap (Jordan, 2026-11-20): "fire arrows should make a small explosion on impact and appear
// flaming while stationary on the tip". Effects layer only (impact-fx.js particles, game pixel coordinates).
// Crossbows: list at EWRAM 0x0203F360 (crossbow.c); arrow slot word 0x0203F2A0 + 8p (low nibble 7 = arrow, byte 1 = type,
// 6 = Fire Arrows, byte 2 = count). Bolts: objects whose touch function (+0x18) is crossbow.c xb_bolt_touch (0x08083061);
// the touch sets the bolt's state (+0x62) to 4 when it strikes something.
(() => {
  const rnd = (a, b) => a + Math.random() * (b - a);
  const bolts = new Map(); let lastT = 0, slotFire = [0, 0];
  const boom = (FX, x, y) => {
    FX.flashes.push({ x, y, t: 0, life: 0.2, r: 26, c: [255, 170, 60] }, { x, y, t: 0, life: 0.1, r: 11, c: [255, 250, 220], body: 1 });
    FX.rings.push({ x, y: y + 3, t: 0, life: 0.34, r0: 3, r1: 24, c: [255, 120, 30], w: 2 });
    for (let i = 0; i < 16; i++) { const a = rnd(0, 6.283), v = rnd(30, 95);
      FX.parts.push({ k: 1, x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.7 - 25, g: 60, t: 0, life: rnd(0.35, 0.8), c0: [255, 230, 140], c1: [230, 60, 10], w: rnd(0.7, 1.3), ph: rnd(0, 6) }); }
    for (let i = 0; i < 8; i++) FX.parts.push({ k: 4, x: x + rnd(-5, 5), y: y + rnd(-3, 3), vx: rnd(-10, 10), vy: rnd(-45, -20), g: 0, t: 0, life: rnd(0.25, 0.45), c0: [255, 220, 120], c1: [255, 70, 10], w: rnd(1.0, 1.6), ph: rnd(0, 6) });
    for (let i = 0; i < 6; i++) FX.parts.push({ k: 2, x: x + rnd(-5, 5), y: y + rnd(-4, 2), vx: rnd(-10, 10), vy: rnd(-20, -6), g: 0, t: 0, life: rnd(0.7, 1.1), r0: rnd(3, 5), r1: rnd(9, 14), a: rnd(0.25, 0.4) });
    FX.shake = Math.max(FX.shake, 3); window.__xbBooms = (window.__xbBooms || 0) + 1;
  };
  setInterval(() => {
    try {
      const FX = window.__FX, M = window.__wideM;
      if (!FX || !FX.live || window.__fxOff || !M || !M._rotk_iwram || !M._rotk_ewram) { bolts.clear(); return; }
      const H8 = M.HEAPU8, ib = M._rotk_iwram(), eb = M._rotk_ewram(), dv = new DataView(H8.buffer);
      if (H8[ib + 0x41B0] !== 1) return;
      const at = (q) => q >= 0x2000000 && q < 0x2040000 ? eb + (q - 0x2000000) : 0;
      const now = performance.now(), dt = Math.min(0.1, (now - (lastT || now)) / 1000); lastT = now;
      for (let p = 0; p < 2; p++) {
        const aw = dv.getUint32(eb + 0x3F2A0 + 8 * p, true);
        if ((aw & 15) === 7 && ((aw >>> 16) & 255) > 0) slotFire[p] = ((aw >>> 8) & 255) === 6 ? now : 0;
        else if (now - slotFire[p] > 600) slotFire[p] = 0;   // the last fire arrow was just shot: its bolt still burns
        const fireNow = (aw & 15) === 7 && ((aw >>> 8) & 255) === 6 && ((aw >>> 16) & 255) > 0;
        if (!fireNow) continue;
        // burning bolt on each ballista's tip
        for (let k = 0; k < Math.min(3, H8[eb + 0x3F390 + p]); k++) {
          const o = at(dv.getUint32(eb + 0x3F360 + p * 24 + k * 8, true)); if (!o) continue;
          if (dv.getUint32(o + 0x14, true) !== 0x08083105 || H8[o + 0x62] === 4) continue;
          const T = (window.__XB_TIP || [])[H8[o + 0x22] & 31]; if (!T) continue;
          const x = dv.getInt16(o + 0xAE, true) - 16 + T[0], y = dv.getInt16(o + 0xB2, true) - 27 + T[1];
          const n = Math.max(1, Math.round(dt * 60));
          for (let i = 0; i < n; i++) FX.parts.push({ k: 4, x: x + rnd(-0.8, 0.8), y: y - 0.5, vx: rnd(-4, 4), vy: rnd(-26, -14), g: -10, t: 0, life: rnd(0.22, 0.38), c0: [255, 235, 160], c1: [255, 70, 10], w: rnd(0.75, 1.05), ph: rnd(0, 6) });
          if (Math.random() < dt * 5) FX.parts.push({ k: 1, x, y: y - 2, vx: rnd(-8, 8), vy: rnd(-40, -22), g: -6, t: 0, life: rnd(0.5, 0.9), c0: [255, 220, 120], c1: [220, 50, 10], w: rnd(0.4, 0.7), ph: rnd(0, 6) });
          if (Math.random() < dt * 2) FX.parts.push({ k: 2, x, y: y - 4, vx: rnd(-3, 3), vy: rnd(-14, -8), g: 0, t: 0, life: rnd(0.6, 0.9), r0: 1, r1: rnd(3, 5), a: 0.18 });
        }
      }
      // fire bolts in flight: a short flame trail, and an explosion where one strikes
      const seen = new Set();
      let ptr = dv.getUint32(ib + 0x3C00, true), n = 0;
      while (at(ptr) && n++ < 400) { const nx = dv.getUint32(at(ptr), true); if (!at(nx)) break; ptr = nx; }
      n = 0;
      while (at(ptr) && n++ < 400) {
        const o = at(ptr);
        if (dv.getUint32(o + 0x18, true) === 0x08083061) {
          let b = bolts.get(ptr);
          if (!b) { const h = at(dv.getUint32(o + 0xC, true)), pl = h ? H8[h + 0x96] & 1 : 0; b = { fire: !!slotFire[pl], done: false }; bolts.set(ptr, b); }
          b.x = dv.getInt16(o + 0xAE, true); b.y = dv.getInt16(o + 0xB2, true) - 4; seen.add(ptr);
          if (b.fire && !b.done) {
            if (H8[o + 0x62] === 4) { b.done = true; boom(FX, b.x, b.y); }
            else if (Math.random() < 0.8) FX.parts.push({ k: 4, x: b.x + rnd(-1, 1), y: b.y, vx: rnd(-6, 6), vy: rnd(-16, -6), g: 0, t: 0, life: rnd(0.12, 0.22), c0: [255, 225, 140], c1: [255, 70, 10], w: rnd(0.6, 0.9), ph: rnd(0, 6) });
          }
        }
        ptr = dv.getUint32(o + 4, true);
      }
      for (const [k, b] of bolts) if (!seen.has(k)) bolts.delete(k);
    } catch (e) {}
  }, 33);
})();
</script>
'''
i = s.rindex("</body>") if "</body>" in s else len(s)
s = s[:i] + FIRE + s[i:]
open(dst, "w", encoding="utf-8").write(s)
print("v208 bolt trap aim / elven / fire patched")
