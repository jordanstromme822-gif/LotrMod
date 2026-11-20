#!/usr/bin/env python3
"""Play Room v222 (Jordan, 2026-11-20): Gandalf's Lightstrike becomes Wisps.

  gandalf-wisps-v222.py in.html out.html original.gba      (in.html already has gandalf-v204 .. v218)

Jordan: no cooldown but castable every 0.5 s; a wisp circles the point where it was summoned, spiralling outward, and
after 5 turns it is gone, having covered about half the screen; 5 damage / level ignoring armor; each enemy it hits
regenerates 1 Shield / level; wisps don't stop at an enemy, which shows a yellow aura where they touch.

ROM (buildGame, the Gandalf block):
  - Lightstrike (entry 1, +40) in all eight tables A-H now uses Gwaihir's handler (0x08040879) and the cast animation
    Dash uses (02 01 05 09), costs WISP_COST Spirit, and its +0x14 halfword is 100: the game's can-cast check for this
    skill (0x08043670) wants hero + 0x9A below +0x14 plus the per-level halfwords after it, all 0 for Lightstrike. The page takes the cast over before the handler runs (gandalf-shield.js).
  - Tables I-P at 0x1601000 + 0x100 * i = A-H with Wisps at 0xFFFF: the page points player + 0x1C there for the half
    second after a cast. The ROM grows to 0x1602000.
  - Text 536 (the Skills page description) re-encoded at 0x1601800.
Page: gandalf-shield.js (swapped in whole) and the skill name "Wisps".
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


TAB = 0x6EE38
ls = rom[TAB + 40:TAB + 80]
assert struct.unpack_from("<I", ls, 0)[0] == 0x08020C45, "Lightstrike entry not where expected"
ent = bytearray(ls)
struct.pack_into("<I", ent, 0, 0x08040879)
struct.pack_into("<I", ent, 4, WISP_COST)
ent[0x20:0x24] = bytes([2, 1, 5, 9])
# The game's "can cast" check for Gandalf's skill 1 (0x08043670) wants hero + 0x9A < +0x14 + the +0x16.. halfwords up
# to the skill level (0x08043764); Lightstrike's are all 0, so it was refused unless the targeting let it through.
struct.pack_into("<h", ent, 0x14, 100)

bank = struct.unpack_from("<I", rom, 0x289A10)[0] - 0x08000000
tsize = struct.unpack_from("<I", rom, bank)[0]
TEXT_AT = 0x1601800
txt = encode(bank, b"Wisps (Level @1) - Gandalf sends out a wisp of light that circles where he stood, spiralling outward"
                   b" for 5 turns. It passes through enemies: each one it touches takes 5 damage / level (armor does not"
                   b" help) and gives Gandalf 1 Shield / level. Can be cast every half second. @2 Spirit.")
assert TEXT_AT + len(txt) <= 0x1602000
tent = bank + 4 + tsize + 4 * 536
js = (
    "          window.__gsBaCd = true;\n"
    "          // v222 Wisps (was Lightstrike, entry 1): casts like Dash in every table A-H; I-P = A-H with Wisps at 0xFFFF (the half\n"
    "          // second after a cast); text 536\n"
    "          if (game.length < 0x1602000) { const g2 = new Uint8Array(0x1602000); g2.set(game); game = g2; }\n"
    f'          [0x6ee38, 0x1600000, 0x1600800, 0x1600900, 0x1600a00, 0x1600b00, 0x1600c00, 0x1600d00].forEach((o, i) => {{ game.set(gHex("{ent.hex()}"), o + 40); const t = game.slice(o, o + 240); t.set([0xff, 0xff, 0, 0], 44); game.set(t, 0x1601000 + 0x100 * i); }});\n'
    f'          game.set(gHex("{txt.hex()}"), {TEXT_AT:#x}); game.set(gHex("{struct.pack("<I", TEXT_AT - bank).hex()}"), {tent:#x});\n'
    "          window.__gsWisp = true;")
rep("          window.__gsBaCd = true;", js)
rep('["Lightning Blade", "Lightstrike", "Shield", "Blinding Aura", "Dash"]', '["Lightning Blade", "Wisps", "Shield", "Blinding Aura", "Dash"]')

head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and "WISP_GAP" not in s[i:j], "unexpected Gandalf block"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s), "text", len(txt))
