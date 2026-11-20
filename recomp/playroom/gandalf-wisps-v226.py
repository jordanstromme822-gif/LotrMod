#!/usr/bin/env python3
"""Play Room v226 (Jordan, 2026-11-20): "Gandalf shouldn't summon an eagle anymore when he casts lightning strike or wisp".

  gandalf-wisps-v226.py in.html out.html original.gba      (in.html already has gandalf-wisps-v222.py)

v222 let the game cast Wisps when Gandalf had a staff in his off hand, through Gwaihir's handler, and the page cleared
the cast before the handler ran; when the game ran ticks between two page frames the eagle still came. Now the game
never casts it:
  - ROM: Wisps (entry 1) costs 0xFFFF in all 16 tables (A-H and the half-second copies I-P), so the game refuses it
    with or without a staff; the page casts every wisp (gandalf-shield.js, swapped in whole).
  - Text 536 names the cost (10 Spirit) instead of the table's @2.
  - The skill buttons' Spirit check (skCostOf) reads 10 for that entry (Gwaihir's handler at 0x08040879 in slot 1).
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst, romp = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
rom = open(romp, "rb").read()
WISP_COST = 10


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit(f"expected {n} got {c}: {a[:100]!r}")
    s = s.replace(a, b)


def encode(bank, text):   # same Huffman coder as gandalf-v206.py
    tree = bank + 4
    codes, todo = {}, [(0x100, [])]
    while todo:
        node, path = todo.pop()
        for bit in (0, 1):
            child = struct.unpack_from("<H", rom, tree + (node - 0x100) * 4 + 2 * bit)[0]
            if child == 0x100: continue
            if child > 0xFF: todo.append((child, path + [bit]))
            else: codes.setdefault(child, path + [bit])
    missing = set(text) - set(codes)
    if missing: raise SystemExit(f"characters not in the text tree: {bytes(sorted(missing))!r}")
    bits = [bb for ch in text + b"\0" for bb in codes[ch]]
    out = bytearray((len(bits) + 7) // 8)
    for i, bb in enumerate(bits): out[i // 8] |= bb << (i % 8)
    return bytes(out)


bank = struct.unpack_from("<I", rom, 0x289A10)[0] - 0x08000000
old_txt = encode(bank, b"Wisps (Level @1) - Gandalf sends out a wisp of light that circles where he stood, spiralling outward"
                       b" for 5 turns. It passes through enemies: each one it touches takes 5 damage / level (armor does not"
                       b" help) and gives Gandalf 1 Shield / level. Can be cast every half second. @2 Spirit.")
new_txt = encode(bank, b"Wisps (Level @1) - Gandalf sends out a wisp of light that circles where he stood, spiralling outward"
                       b" for 5 turns. It passes through enemies: each one it touches takes 5 damage / level (armor does not"
                       b" help) and gives Gandalf 1 Shield / level. Can be cast every half second. %d Spirit." % WISP_COST)
assert 0x1601800 + len(new_txt) <= 0x1602000
rep(f'game.set(gHex("{old_txt.hex()}"), 0x1601800);', f'game.set(gHex("{new_txt.hex()}"), 0x1601800);')
# every table: Wisps at 0xFFFF (A-H written here, I-P are copies made right after with 0xFFFF already)
rep("game.set(t, 0x1601000 + 0x100 * i); });",
    "game.set(t, 0x1601000 + 0x100 * i); game.set([0xff, 0xff, 0, 0], o + 44); });   // v226: the game never casts Wisps")
rep("const o = t - 0x08000000 + 40 * s; return (R[o] | R[o + 1] | R[o + 2] | R[o + 3]) ? R[o + 4] | R[o + 5] << 8 : -1; };",
    f"const o = t - 0x08000000 + 40 * s; if (s === 1 && R[o] === 0x79 && R[o + 1] === 0x08 && R[o + 2] === 0x04 && R[o + 3] === 0x08) return {WISP_COST};   // v226: Wisps, cast by the page\n"
    "          return (R[o] | R[o + 1] | R[o + 2] | R[o + 3]) ? R[o + 4] | R[o + 5] << 8 : -1; };")

head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and "WISP_GAP" in s[i:j], "unexpected Gandalf block"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
