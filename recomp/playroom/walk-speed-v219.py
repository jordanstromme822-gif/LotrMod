# v219 walk cycle keeps pace with speed bonuses for every hero (Jordan, 2026-11-20: "walking around doesn't feel natural,
# is the movement not drawn in increments of 5% to match game speed increases up to 75%"). The v111 code counted a
# 12-picture walk, but the walks now have 16 pictures (and some heroes other counts), so the extra pictures stopped at
# picture 12 and wrapped wrong: the feet slid at higher speeds. Now: the picture count comes from the hero's own
# animation (as tools/feel/feel.c reads it), and the share comes from the game's own walk speed (hero + 0xE4, which the
# game sets to 3 px x (100 + Speed) / 100, capped at +75%, 0x080237F2), in 5% steps.
#   python3 walk-speed-v219.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)
rep("""            const a = r8(hero + 0x22), x = r16(hero + 0xae), y = r16(hero + 0xb2);
            if (a === walkA) return;
            const extra = Math.min(15, Math.max(0, Math.floor((r16(P + 0xD4) << 16 >> 16) / 5))) * 0.05, moved = walkA >= 0 && (x !== walkX || y !== walkY);
            const d = (a - walkA + 12) % 12;
            walkA = a; walkX = x; walkY = y;
            if (!moved || extra <= 0.01 || a >= 12 || d < 1 || d > 3) { walkAcc = 0; return; }
            walkAcc += d * extra;
            const add = Math.floor(walkAcc); if (add < 1) return;
            walkAcc -= add; const n = (a + add) % 12;""",
"""            const a = r8(hero + 0x22), x = r16(hero + 0xae), y = r16(hero + 0xb2);
            if (a === walkA) return;
            // v219: the walk's own picture count (animation entry + 0x24 -> + 4 -> byte 6), and the game's own speed (+0xE4)
            const ent = r32(hero + 0x24); let nf = walkNf.get(ent);
            if (nf === undefined) { nf = 12; try { const R = window.__romFull, e = ent - 0x08000000, b = (R[e + 4] | R[e + 5] << 8 | R[e + 6] << 16 | R[e + 7] << 24) - 0x08000000; if (R[b + 6] > 1 && R[b + 6] <= 32) nf = R[b + 6]; } catch (e) {} walkNf.set(ent, nf); }
            const spd = r32(hero + 0xE4) | 0, extra = Math.min(15, Math.max(0, Math.floor((spd / 196608 - 1) * 20 + 0.001))) * 0.05, moved = walkA >= 0 && (x !== walkX || y !== walkY);
            const d = (a - walkA + nf) % nf;
            walkA = a; walkX = x; walkY = y;
            if (!moved || extra <= 0.01 || a >= nf || d < 1 || d > 3) { walkAcc = 0; return; }
            walkAcc += d * extra;
            const add = Math.floor(walkAcc); if (add < 1) return;
            walkAcc -= add; const n = (a + add) % nf;""")
rep("""        let walkA = -1, walkX = -1, walkY = -1, walkAcc = 0;""", """        let walkA = -1, walkX = -1, walkY = -1, walkAcc = 0; const walkNf = new Map();""")
open(out, "w", encoding="utf-8").write(s); print("ok walk speed")
