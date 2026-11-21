#!/usr/bin/env python3
"""Play Room v233 (Jordan, 2026-11-21): "Wisps should stop and do the animation to cast them, you can't move and cast wisps at the same time".

  gandalf-wisps-v233.py in.html out.html original.gba      (in.html already has gandalf-wisps-v232.py)

  - gandalf-shield.js (swapped in whole): every cast stops him for the staff-raise pose, walking or standing (undoes
    v232's walk-through casting).
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
head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and "WISP_GAP" in s[i:j], "unexpected Gandalf block"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
