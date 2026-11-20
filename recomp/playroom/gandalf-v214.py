#!/usr/bin/env python3
"""Play Room v214 (Jordan, 2026-11-20): Blinding Aura shows its new animation at every graphics setting and has a
15 s cooldown that counts down on its button.

  gandalf-v214.py in.html out.html original.gba      (in.html already has gandalf-v204 .. v206)

ROM (buildGame, the Gandalf block): tables E-H at 0x1600A00 + 0x100 * i are copies of A-D (0x6EE38, 0x1600000,
  0x1600800, 0x1600900) with Blinding Aura (entry 3, cost at +4) at 0xFFFF, so while it cools the game refuses it and
  takes no Spirit. Text 538 is rewritten at 0x1600E00 to name the cooldown.
Page: gandalf-shield.js (swapped in whole: canvas burst, cooldown, cast seen from the cast flags) and the button
  countdown for Blinding Aura (hero 3, skill 3).
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst, romp = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
rom = open(romp, "rb").read()
BA_SEC = 15


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
tsize = struct.unpack_from("<I", rom, bank)[0]
TEXT_AT = 0x1600E00
txt = encode(bank, b"Blinding Aura (Level @1) - Foes within twice the old range take 10 damage +2 / level and are blinded for"
                   b" 3 seconds. Refills Gandalf's Shield to full. %d second cooldown. @2 Spirit." % BA_SEC)
assert TEXT_AT + len(txt) <= 0x1601000
ent = bank + 4 + tsize + 4 * 538
js = (
    "          // v214: tables E-H = A-D with Blinding Aura (entry 3) at cost 0xFFFF while it cools; text 538 names the cooldown\n"
    "          [0x6ee38, 0x1600000, 0x1600800, 0x1600900].forEach((o, i) => { const t = game.slice(o, o + 240); t.set([0xff, 0xff, 0, 0], 124); game.set(t, 0x1600a00 + 0x100 * i); });\n"
    f'          game.set(gHex("{txt.hex()}"), {TEXT_AT:#x}); game.set(gHex("{struct.pack("<I", TEXT_AT - bank).hex()}"), {ent:#x});\n'
    "          window.__gsBaCd = true;\n"
    "          window.__gsDash = true;")
rep("          window.__gsDash = true;", js)

rep("const cdOf = (v) => v && v[0] === 3 && v[1] === 0 && lbLeft > 0 ? [lbLeft, 20] : ",
    f"let baLeft = 0; try {{ baLeft = window.__baLeft ? window.__baLeft() : 0; }} catch (e) {{}}\n"
    f"        const cdOf = (v) => v && v[0] === 3 && v[1] === 0 && lbLeft > 0 ? [lbLeft, 20] : v && v[0] === 3 && v[1] === 3 && baLeft > 0 ? [baLeft, {BA_SEC}] : ")

head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j]
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
