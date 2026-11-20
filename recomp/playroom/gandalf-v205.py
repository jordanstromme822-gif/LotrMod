#!/usr/bin/env python3
"""Play Room v205 (Jordan, 2026-11-20): every sword strike refills Gandalf's Shield (by Lightning Blade's level, with or
without Lightning Blade up); casting Lightning Blade stuns every foe near Gandalf.

  gandalf-v205.py in.html out.html original.gba      (in.html already has gandalf-v204.py)

Swaps the page module for the new gandalf-shield.js and re-encodes texts 535 / 537 (same place, ROM 0x1600100).
"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst, romp = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
rom = open(romp, "rb").read()
TEXT_AT, END = 0x1600100, 0x1601000
TEXTS = [(535, b"Lightning Blade (Level @1) - Lightning bursts from Gandalf, stunning every enemy near him for 4 seconds,"
               b" and his sword glows: +3 damage / level for 10 seconds. 20 second cooldown. @2 Spirit."),
         (537, b"Shield (Level @1) - Always on: soaks up 20 damage / level. It fades over time (Spirit Regen slows it)."
               b" Every sword strike refills it 5 / Lightning Blade level.")]


def encode(bank, text):
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
    bits = [b for ch in text + b"\0" for b in codes[ch]]
    out = bytearray((len(bits) + 7) // 8)
    for i, b in enumerate(bits): out[i // 8] |= b << (i % 8)
    return bytes(out)


bank = struct.unpack_from("<I", rom, 0x289A10)[0] - 0x08000000
tsize = struct.unpack_from("<I", rom, bank)[0]
at = TEXT_AT
for idx, t in TEXTS:
    e = encode(bank, t)
    ent = bank + 4 + tsize + 4 * idx
    old = rom[ent:ent + 4].hex()
    pat = re.compile(r'          if \(gEq\(%#x, "%s"\)\) \{ game\.set\(gHex\("[0-9a-f]+"\), 0x[0-9a-f]+\); game\.set\(gHex\("[0-9a-f]+"\), %#x\); \}' % (ent, old, ent))
    new = f'          if (gEq({ent:#x}, "{old}")) {{ game.set(gHex("{e.hex()}"), {at:#x}); game.set(gHex("{struct.pack("<I", at - bank).hex()}"), {ent:#x}); }}'
    s, n = pat.subn(lambda m: new, s)
    if n != 1: raise SystemExit(f"text {idx}: {n} sites")
    at = (at + len(e) + 3) & ~3
assert at <= END
s = s.replace("// Gandalf (v204, Jordan 2026-11-20): Shield always on", "// Gandalf (v204-v205, Jordan 2026-11-20): Shield always on", 1)

# the page module: replace the v204 block (it starts with its first comment line and ends at its own "  })();")
head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and s[i:j].rstrip().endswith("requestAnimationFrame(draw);\n  })();"), "block bounds"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
