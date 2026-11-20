#!/usr/bin/env python3
"""Play Room v202 (Jordan, 2026-11-20): Frodo's Bolt Trap.

  bolt-trap-v202.py in.html out.html

- Set-up time: a new Bolt Trap crossbow waits 1.0 s before its first bolt at Bolt Trap level 1, 0.1 s less a level
  (0.9, 0.8, 0.7, 0.6 s at level 5). Was 1/3 s at every level. The page raises the crossbow's reload counter (crossbow.c
  list entry + 7, game ticks, 30 a second) right after the crossbow shows up. Quick Drop's crossbows keep the short
  wait (it is the quick one).
- The wait between two Bolt Traps (v168) is 2.5 s instead of 3 s (75 game ticks), with the countdown on the button.
- Both now cover P2's Frodo in a one-game P2 game too (player 1 in game 0), not just the page's own player.
  Online: each page still does its own player; the writes travel with the buttons (v180).
- Bigger crossbow: 1.5x pictures (24x24 in a 32x32 sprite; tools/xbbig/xbbig.py -> xbbig.bin at ROM 0x95000, freed
  Spanish text bank). The 16-facing anim set of tools/turn16 (xb16_anim 0x0809FB04 / xb16_frames 0x0809F9B8, data
  only, so the engine's compiled copy of turn16 is unchanged) points at the new pictures.
- Glow: the bolt tip gets a glowing whitish-blue light and the bow string a faint blue glow (lighting pass, positions
  per facing from tools/xbbig/xbbig.json).
"""
import json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
big = open(os.path.join(ROOT, "tools", "xbbig", "xbbig.bin"), "rb").read()
meta = json.load(open(os.path.join(ROOT, "tools", "xbbig", "xbbig.json")))
assert len(big) == 8192

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:90]!r}")
    s = s.replace(old, new)

# ---- ROM: bigger pictures + the 16-facing anim set pointing at them ----
m = re.search(r'game\.set\(hexBytes\("([0-9a-f]+)"\), 0x9F000\);', s)
t16 = bytearray(bytes.fromhex(m.group(1)))
FR, AN = 0x9B8, 0xB04                          # xb16_frames, xb16_anim (tools/turn16/turn16.sym) - 0x0809F000
assert t16[FR:FR + 12] == bytes([0x20, 0x10, 0, 0, 0, 0, 0x10, 0, 0, 1, 0, 1]), "turn16 frames header moved"
assert struct.unpack_from("<I", t16, AN)[0] == 0x08094400 and struct.unpack_from("<I", t16, AN + 4)[0] == 0x0809F9B8
struct.pack_into("<H", t16, FR + 8, 0x200)     # biggest frame: 512 bytes
part = (-16 & 0x1FF) | ((-27 & 0x1FF) << 9) | (2 << 18)   # one 32x32 part (shape 0, size 2), bottom where it was
for n in range(16):
    r = FR + 0x2C + n * 0x12                    # records: 12-byte header + 16 offsets (from + 0xC: 0x20 + 0x12 n)
    assert t16[r] == 1 and t16[r + 2] == 0x10 and t16[r + 3] == 0x10
    t16[r + 2] = t16[r + 3] = 0x20
    struct.pack_into("<HH", t16, r + 4, n * 0x200, 0x200)
    struct.pack_into("<I", t16, r + 14, part)
struct.pack_into("<I", t16, AN, 0x08095000)
s = s[:m.start(1)] + t16.hex() + s[m.end(1):]
# The Orc Head code was rebuilt after v171, so crossbow.c's xb_anim / xb_update moved (0x080852D0 / 0x08083105) and
# turn16's compiled check (0x08084408 / 0x08082231) no longer finds the crossbows: they stayed on crossbow.c's own
# 8-way 16x16 set. Point that set at the big pictures and the 16-frame records instead (frames 0-7 are the same 8
# facings, which crossbow.c's fire() picks).
m = re.search(r'game\.set\(hexBytes\("([0-9a-f]+)"\), 0x7F000\);', s)
orc = bytearray(bytes.fromhex(m.group(1)))
XA = 0x852D0 - 0x7F000
assert struct.unpack_from("<IIII", orc, XA) == (0x08085300, 0x08085224, 0, 1), "crossbow.c xb_anim moved"
struct.pack_into("<II", orc, XA, 0x08095000, 0x0809F9B8)
s = s[:m.start(1)] + orc.hex() + s[m.end(1):]
rep('0x94400); // crossbow trap, 16 facings (tools/turn16/xb16.py)',
    '0x94400); // crossbow trap, 16 facings (tools/turn16/xb16.py)\n'
    '      game.set(hexBytes("%s"), 0x95000); // v202: crossbow trap 1.5x, 32x32 sprites (tools/xbbig/xbbig.py)' % big.hex())

# ---- set-up time + 2.5 s wait (replaces v168's loop) ----
A = s.index("        const BT_TICKS = 90;")
B = s.index("        window.__bPick = (any, range) => {", A)
old = s[A:B]
assert "btSeen" in old and old.count("setInterval(") == 1
new = '''        // v202 (Jordan, 2026-11-20): a new Bolt Trap crossbow takes time to set up before its first bolt: 1.0 s at Bolt Trap
        // level 1, 0.1 s less a level (0.6 s at 5). The page raises its reload counter (list entry + 7, game ticks) as soon
        // as it shows up. The wait between two Bolt Traps is 2.5 s (75 ticks; was 3 s). One-game P2: P2's Frodo
        // (player 1 in game 0) too. Online: each page does its own player (the writes travel with the buttons).
        const BT_TICKS = 75, BT_SEC = BT_TICKS / 30;
        const btSetup = (L) => 30 - 3 * (Math.max(1, Math.min(5, L)) - 1);
        const btSt = [0, 1].map(() => ({ seen: new Set(), obj: 0, end: 0, qd: -1, locked: false }));
        const btWrite = (a, v) => {
          const mp = window.__mp, M = mp && mp.M;
          if (M && M._rotk_link_on && M._rotk_link_on() && M._rotk_link_ewram) { for (const m of [0, 1]) M.HEAPU8[M._rotk_link_ewram(m) + (a & 0x3ffff)] = v; }
          else { const o = at(a); if (o >= 0) H8[o] = v; }
        };
        const btNow = () => r32(0x030041A4);
        const btOne = () => { try { const M = window.__wideM; return !(window.__mp && window.__mp.online) && !!(M && M._rotk_link_is_one && M._rotk_link_is_one()); } catch (e) { return false; } };
        window.__btLeft = (pp) => { try { const st = btSt[pp == null ? r8(0x03003F59) & 1 : pp & 1]; if (!st.locked) return 0; const d = (st.end - btNow()) | 0; return d > 0 ? d / 30 : 0; } catch (e) { return 0; } };
        window.__btSec = BT_SEC;
        setInterval(() => {
          try {
            if (iwram < 0 || (window.__mp && window.__mp.online && !window.__mp.sync)) return;
            ew = findEw(); H8 = heap(); if (ew < 0) return;
            const me = r8(0x03003F59) & 1, now = btNow(), menu = inMenu();
            for (const pl of btOne() ? [0, 1] : [me]) {
              const st = btSt[pl], P = 0x03003C00 + 0x1AC * pl, hero = r32(P);
              if (hero >>> 24 !== 2 || r8(P + 0x19F) !== 0) { st.seen = new Set(); st.obj = 0; st.locked = false; continue; }
              if (hero !== st.obj) { st.obj = hero; st.seen = new Set(); st.locked = false; st.qd = -1; }
              const n = Math.min(3, r8(0x0203F390 + pl)), qd = r32(0x0203F500 + 4 * pl);
              const cur = new Set(); let fresh = false;
              for (let k = 0; k < n; k++) {
                const e = 0x0203F360 + pl * 24 + k * 8, o = r32(e); cur.add(o);
                if (!o || st.seen.has(o) || st.qd < 0 || qd !== st.qd || menu) continue;
                fresh = true;
                // set-up: the crossbow starts with 10 ticks before its first bolt; make it the level's set-up time
                const cd = r8(e + 7), want = btSetup(r8(P + 0x171)) - (10 - cd);
                if (r8(e + 6) === 10 && cd > 0 && want > cd) btWrite(e + 7, Math.min(255, want));
              }
              if (fresh) { st.end = (now + BT_TICKS) | 0; st.locked = true; }
              st.seen = cur; st.qd = qd;
              const lock = st.locked && ((st.end - now) | 0) > 0;
              if (!lock) st.locked = false;
              const v = lock ? 0x7F : 0;
              if (r8(hero + 0x9A) !== v && (lock || r8(hero + 0x9A) === 0x7F)) btWrite(hero + 0x9A, v);
            }
          } catch (e) {}
        }, 50);
'''
s = s[:A] + new + s[B:]
rep("v[1] === 1 && btLeft > 0 ? [btLeft, 3] : null;", "v[1] === 1 && btLeft > 0 ? [btLeft, window.__btSec || 2.5] : null;")

# ---- glow on the bolt tip and the string ----
rep("uniform vec3 TrapP[6];", "uniform vec3 TrapP[6]; uniform vec4 TrapT[6]; uniform vec4 TrapS[6];", 2)
GLOW = (
    "  // ---- v202: the crossbow's bolt tip glows whitish blue, its string a faint blue ----\\n"
    "  for (int i = 0; i < 6; i++) {\\n"
    "    if (TrapT[i].z < 0.001) continue;\\n"
    "    float pu = 0.85 + 0.15 * sin(Time * 3.1 + float(i) * 2.3);\\n"
    "    vec2 d = (v - TrapT[i].xy) / GPx; float r2 = dot(d, d);\\n"
    "    float tc = exp(-r2 / 1.4) * 0.95 * pu, th = exp(-r2 / 14.0) * 0.55 * pu * mix(1.0, 1.35, Night);\\n"
    "    vec3 tg = vec3(0.92, 0.97, 1.0) * tc + vec3(0.42, 0.68, 1.0) * th;\\n"
    "    vec2 a0 = TrapS[i].xy, a1 = TrapS[i].zw, ab = (a1 - a0) / GPx, ap = (v - a0) / GPx;\\n"
    "    float tt = clamp(dot(ap, ab) / max(dot(ab, ab), 0.0001), 0.0, 1.0); vec2 q2 = ap - ab * tt;\\n"
    "    float sg = (exp(-dot(q2, q2) / 0.9) * 0.32 + exp(-dot(q2, q2) / 6.0) * 0.16) * mix(1.0, 1.3, Night);\\n"
    "    tg += vec3(0.45, 0.7, 1.0) * sg * TrapT[i].w;\\n"
    "    c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(tg * TrapT[i].z, 0.0, 1.0));\\n"
    "  }\\n"
    "  c = mix(c, cPre, hud);")
rep("  }\\n  c = mix(c, cPre, hud);", "  }\\n" + GLOW, 2)

TIP = [t or [16, 16] for t in meta["tip"]]
BOW = [b or [16, 16, 16, 16] for b in meta["bow"]]
rep("  const trapU = new Float32Array(18);",
    "  const trapU = new Float32Array(18), trapTU = new Float32Array(24), trapSU = new Float32Array(24);\n"
    "  // v202: bolt tip and bow per picture (tools/xbbig/xbbig.json, 32x32 sprite pixels; the sprite sits at object - (16, 27))\n"
    "  const XB_TIP = %s, XB_BOW = %s;\n"
    "  const trapGlow = (w, h) => {\n"
    "    const out = [];\n"
    "    try {\n"
    "      const M = window.__wideM; if (!M || !M._rotk_iwram || !M._rotk_ewram) return out;\n"
    "      const H8 = M.HEAPU8, ib = M._rotk_iwram(), eb = M._rotk_ewram(), dv = new DataView(H8.buffer);\n"
    "      if (H8[ib + 0x41B0] !== 1) return out;\n"
    "      const cx = dv.getInt32(ib + 0x20F8, true), cy = dv.getInt32(ib + 0x20FC, true);\n"
    "      for (let p = 0; p < 2; p++) for (let k = 0; k < Math.min(3, H8[eb + 0x3F390 + p]); k++) {\n"
    "        const ptr = dv.getUint32(eb + 0x3F360 + p * 24 + k * 8, true);\n"
    "        if (ptr < 0x2000000 || ptr >= 0x2040000) continue;\n"
    "        const o = eb + (ptr - 0x2000000);\n"
    "        const up = dv.getUint32(o + 0x14, true), an = dv.getUint32(o + 0x24, true);\n"
    "        if ((up !== 0x08083105 && up !== 0x08082231) || H8[o + 0x62] === 4 || (an !== 0x080852D0 && an !== 0x0809FB04)) continue;\n"
    "        const f = H8[o + 0x22] & 15, x0 = dv.getInt16(o + 0xAE, true) - cx + (w - 240) / 2 - 16, y0 = dv.getInt16(o + 0xB2, true) - cy + (h - 160) / 2 - 27;\n"
    "        const t = XB_TIP[f], b = XB_BOW[f];\n"
    "        out.push([x0 + t[0], y0 + t[1], x0 + b[0], y0 + b[1], x0 + b[2], y0 + b[3]]);\n"
    "      }\n"
    "    } catch (e) {}\n"
    "    return out;\n"
    "  };" % (json.dumps(TIP), json.dumps(BOW)))
rep("            gl.uniform3fv(fu[\"TrapP[0]\"], trapU); }",
    "            gl.uniform3fv(fu[\"TrapP[0]\"], trapU); }\n"
    "          if (fu[\"TrapT[0]\"]) { const tg = window.__trapOff ? [] : trapGlow(stride, h); trapTU.fill(0); trapSU.fill(0);\n"
    "            tg.slice(0, 6).forEach((q, i) => { trapTU.set([(q[0] - sx) / w, (q[1] - sy) / h, 1, 1], 4 * i); trapSU.set([(q[2] - sx) / w, (q[3] - sy) / h, (q[4] - sx) / w, (q[5] - sy) / h], 4 * i); });\n"
    "            gl.uniform4fv(fu[\"TrapT[0]\"], trapTU); if (fu[\"TrapS[0]\"]) gl.uniform4fv(fu[\"TrapS[0]\"], trapSU); }")
rep("        if (dv.getUint32(o + 0x14, true) !== 0x08082231 || H8[o + 0x62] === 4) continue;\n        out.push([dv.getInt16(o + 0xAE, true) - cx",
    "        { const up = dv.getUint32(o + 0x14, true); if ((up !== 0x08083105 && up !== 0x08082231) || H8[o + 0x62] === 4) continue; }   // v202: xb_update moved (Orc Head code rebuilt)\n        out.push([dv.getInt16(o + 0xAE, true) - cx")
open(dst, "w", encoding="utf-8").write(s)
print("v202 bolt trap patched")
