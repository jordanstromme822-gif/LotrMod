#!/usr/bin/env python3
"""Play Room v230 (Jordan, 2026-11-21): "Change whisp summon to 2.5 revolutions that last approx 4.8 seconds all rotating
clockwise with a .7 second delay in between cast times make an animation of Gandalf raising his staff to summon the whisp
out the top of it".

  gandalf-wisps-v230.py in.html out.html original.gba      (in.html already has gandalf-wisps-v227.py)

  - gandalf-shield.js (swapped in whole): WISP_TURNS 2.5 x WISP_TURN 57.6 ticks (4.8 s), clockwise only, WISP_GAP 21 ticks
    (0.7 s); each cast plays the game's spell-cast pose (staff raised) and the wisp comes out of the staff top.
  - Text 536: 2.5 turns, 0.7 s.
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
                       b" for 7 turns. It passes through enemies: each one it touches takes 5 damage / level (armor does not"
                       b" help) and gives Gandalf 1 Shield / level. Hold to keep casting, one every half second. %d Spirit." % WISP_COST)
new_txt = encode(bank, b"Wisps (Level @1) - Gandalf raises his staff and a wisp of light rises from it, circling where he stood"
                       b" and spiralling outward for 2 and a half turns. It passes through enemies: each one it touches takes"
                       b" 5 damage / level (armor does not help) and gives Gandalf 1 Shield / level. Hold to keep casting,"
                       b" one every 0.7 seconds. %d Spirit." % WISP_COST)
assert 0x1601800 + len(new_txt) <= 0x1602000
rep(f'game.set(gHex("{old_txt.hex()}"), 0x1601800);', f'game.set(gHex("{new_txt.hex()}"), 0x1601800);')
head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and "WISP_GAP" in s[i:j], "unexpected Gandalf block"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
