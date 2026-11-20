#!/usr/bin/env python3
"""Play Room v206 (Jordan, 2026-11-20): Blinding Aura refills Gandalf's Shield and reaches twice as far, looking like
his own aura; Summon Gwaihir becomes Dash (4 s cooldown, through enemies; +10 Shield per foe while Lightning Blade is up).

  gandalf-v206.py in.html out.html original.gba      (in.html already has gandalf-v204.py + v205)

ROM (buildGame, the v204 block):
  - Gandalf's table 0x6EE38: Summon Gwaihir (skill 4) costs DASH_COST and casts like Lightstrike (+0x20..0x23
    02 01 05 09: an attack-type skill whose handler waits for the cast animation), so the page sees the cast
    (player + 0x1A3 = 4, + 0x1A5 bit 0) and turns it into the dash before Gwaihir comes.
  - Four tables: A 0x6EE38 (ready), B 0x1600000 (Lightning Blade cooling: its cost 0xFFFF), C 0x1600800 (Dash cooling),
    D 0x1600900 (both). The page points player + 0x1C at the right one.
  - Texts 538 (Blinding Aura) and 539 (Dash) at 0x1600300.
Page: gandalf-shield.js (swapped in whole), shader aura scale / burst uniforms, skill name + Skills countdown.
"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst, romp = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
rom = open(romp, "rb").read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit(f"expected {n} got {c}: {a[:100]!r}")
    s = s.replace(a, b)


TAB, TAB_B, TAB_C, TAB_D, TEXT_AT = 0x6EE38, 0x1600000, 0x1600800, 0x1600900, 0x1600300
DASH_COST = 20
orig = rom[TAB:TAB + 240]
assert struct.unpack_from("<I", orig, 160)[0] == 0x08040879
a = bytearray(orig)
struct.pack_into("<6h", a, 0x14, 300, 0, 0, 0, 0, 0)        # Lightning Blade: 10 s at every level (v204)
struct.pack_into("<I", a, 80 + 4, 0xFFFF)                     # Shield: never cast (v204)
struct.pack_into("<I", a, 160 + 4, DASH_COST)                 # Dash
a[160 + 0x20:160 + 0x24] = bytes([2, 1, 5, 9])
b = bytearray(a); struct.pack_into("<I", b, 4, 0xFFFF)
c = bytearray(a); struct.pack_into("<I", c, 160 + 4, 0xFFFF)
d = bytearray(b); struct.pack_into("<I", d, 160 + 4, 0xFFFF)
H = lambda x: bytes(x).hex()
blk_i = s.index('if (gEq(0x6ee38, "' + H(orig) + '")) {')
blk_j = s.index("window.__gsTabB = true;", blk_i)
blk = s[blk_i:blk_j]
blk2, n1 = re.subn(r'game\.set\(gHex\("[0-9a-f]+"\), 0x6ee38\);', lambda m: f'game.set(gHex("{H(a)}"), 0x6ee38);', blk)
blk2, n2 = re.subn(r'game\.set\(gHex\("[0-9a-f]+"\), 0x1600000\);', lambda m: f'game.set(gHex("{H(b)}"), 0x1600000); game.set(gHex("{H(c)}"), {TAB_C:#x}); game.set(gHex("{H(d)}"), {TAB_D:#x});', blk2)
assert n1 == 1 and n2 == 1, (n1, n2)

TEXTS = [(538, b"Blinding Aura (Level @1) - Foes within twice the old range take 10 damage +2 / level and are blinded for"
               b" 3 seconds. Refills Gandalf's Shield to full. @2 Spirit."),
         (539, b"Dash (Level @1) - Gandalf dashes forward through enemies. While Lightning Blade is up, each enemy he"
               b" dashes through restores 10 Shield. 4 second cooldown. @2 Spirit.")]


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
    bits = [bb for ch in text + b"\0" for bb in codes[ch]]
    out = bytearray((len(bits) + 7) // 8)
    for i, bb in enumerate(bits): out[i // 8] |= bb << (i % 8)
    return bytes(out)


bank = struct.unpack_from("<I", rom, 0x289A10)[0] - 0x08000000
tsize = struct.unpack_from("<I", rom, bank)[0]
at, lines = TEXT_AT, []
for idx, t in TEXTS:
    e = encode(bank, t)
    ent = bank + 4 + tsize + 4 * idx
    lines.append(f'          if (gEq({ent:#x}, "{rom[ent:ent + 4].hex()}")) {{ game.set(gHex("{e.hex()}"), {at:#x}); game.set(gHex("{struct.pack("<I", at - bank).hex()}"), {ent:#x}); }}')
    at = (at + len(e) + 3) & ~3
assert at <= TAB_C
blk2 += "\n".join(lines).lstrip() + "\n          window.__gsDash = true;\n          "
s = s[:blk_i] + blk2 + s[blk_j:]
s = s.replace("// Gandalf (v204-v205, Jordan 2026-11-20): Shield always on", "// Gandalf (v204-v206, Jordan 2026-11-20): Shield always on", 1)

# skill name and the Skills countdown for Dash
rep('["Lightning Blade", "Lightstrike", "Shield", "Blinding Aura", "Summon Gwaihir"]', '["Lightning Blade", "Lightstrike", "Shield", "Blinding Aura", "Dash"]')
rep("const cdOf = (v) => v && v[0] === 3 && v[1] === 0 && lbLeft > 0 ? [lbLeft, 20] : cdOf0(v);",
    "let dashLeft = 0; try { dashLeft = window.__dashLeft ? window.__dashLeft() : 0; } catch (e) {}\n"
    "        const cdOf = (v) => v && v[0] === 3 && v[1] === 0 && lbLeft > 0 ? [lbLeft, 20] : v && v[0] === 3 && v[1] === 4 && dashLeft > 0 ? [dashLeft, 4] : cdOf0(v);")

# shader: the aura can grow (AuraS, Blinding Aura at twice the range) and brighten (AuraX)
rep("uniform float AuraB, AuraW;", "uniform float AuraB, AuraW, AuraS, AuraX;", 2)
rep("vec2 d = (v - AuraP) / GPx; float r2 = dot(d, d);\\n    float a = exp(-r2 / 420.0)",
    "vec2 d = (v - AuraP) / GPx / max(AuraS, 1.0); float r2 = dot(d, d);\\n    float a = exp(-r2 / 420.0)", 2)
rep("* a * AuraK * (1.0 + 0.3 * AuraB)", "* a * AuraK * (1.0 + 0.3 * AuraB + AuraX)", 2)
n = s.count("if (fu.AuraW) gl.uniform1f(fu.AuraW, window.__lbGlow || 0);")
assert n >= 1
s = s.replace("if (fu.AuraW) gl.uniform1f(fu.AuraW, window.__lbGlow || 0);",
              "if (fu.AuraW) gl.uniform1f(fu.AuraW, window.__lbGlow || 0); if (fu.AuraS) gl.uniform1f(fu.AuraS, window.__auraS || 1); if (fu.AuraX) gl.uniform1f(fu.AuraX, window.__auraX || 0);")

# the page module
head = "  // Gandalf's always-on Shield and Lightning Blade"
i = s.index(head); assert s.count(head) == 1
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and s[i:j].rstrip().endswith("requestAnimationFrame(draw);\n  })();"), "block bounds"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s), "aura setter sites", n)
