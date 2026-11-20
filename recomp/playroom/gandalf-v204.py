#!/usr/bin/env python3
"""Play Room v204 (Jordan, 2026-11-20): Gandalf's Shield is always on and drains; Sword of Power becomes Lightning Blade.

  gandalf-v204.py in.html out.html original.gba

ROM (buildGame, after every other change):
  - Gandalf's skill table 0x6EE38 (40 bytes a skill): Lightning Blade (skill 0) lasts 10 s at every level (+0x14
    halfwords 300, 0, ...; was 270 / level), keeps +3 damage / level. Shield (skill 2) costs 0xFFFF, so the game never
    casts it (no bubble, no cast animation); the page runs it instead (gandalf-shield.js).
  - A copy of that table at ROM 0x1600000 (CPU 0x09600000) whose Lightning Blade also costs 0xFFFF: the page points
    player + 0x1C at it for the 20 s cooldown. The ROM grows to 0x1601000 if it is shorter.
  - Texts 535 (Lightning Blade) and 537 (Shield) re-encoded with the English bank's tree at ROM 0x1600100.
Page: gandalf-shield.js (shield, drain, strikes, cooldown, XP vial, sword glow), aura colour follows the shield, the
Skills buttons know the new name / 10 s / the cooldown, and Shield gets no cast button.
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
src, dst, romp = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
rom = open(romp, "rb").read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: raise SystemExit(f"expected {n} got {c}: {a[:100]!r}")
    s = s.replace(a, b)


TAB, TAB_B, TEXT_AT = 0x6EE38, 0x1600000, 0x1600100
orig = rom[TAB:TAB + 240]
assert struct.unpack_from("<I", orig, 0)[0] == 0x08044C91 and struct.unpack_from("<6h", orig, 0x14) == (0, 270, 270, 270, 270, 270)
assert struct.unpack_from("<I", orig, 80)[0] == 0x08020CA1
new = bytearray(orig)
struct.pack_into("<6h", new, 0x14, 300, 0, 0, 0, 0, 0)       # Lightning Blade: 10 s at every level
struct.pack_into("<I", new, 80 + 4, 0xFFFF)                    # Shield: never cast
cool = bytearray(new)
struct.pack_into("<I", cool, 4, 0xFFFF)                        # Lightning Blade while it cools down

TEXTS = [(535, b"Lightning Blade (Level @1) - Gandalf's sword glows with lightning: +3 damage / level for 10 seconds."
               b" Each strike refills his Shield 5 / level. 20 second cooldown. @2 Spirit."),
         (537, b"Shield (Level @1) - Always on: soaks up 20 damage / level. It fades over time (Spirit Regen slows it)"
               b" and Lightning Blade strikes refill it.")]


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
tset, at = [], TEXT_AT
for idx, t in TEXTS:
    e = encode(bank, t)
    ent = bank + 4 + tsize + 4 * idx
    tset.append((at, e.hex(), ent, struct.pack("<I", at - bank).hex(), rom[ent:ent + 4].hex()))
    at = (at + len(e) + 3) & ~3
assert at <= TAB_B + 0x1000

H = lambda b: bytes(b).hex()
lines = ["      // Gandalf (v204, Jordan 2026-11-20): Shield always on (never cast: cost 0xFFFF), Sword of Power is Lightning Blade",
         "      // (10 s, +3 damage / level, strikes refill the shield; 20 s cooldown through the table copy at 0x1600000).",
         "      // recomp/playroom/gandalf-v204.py + gandalf-shield.js.",
         "      {",
         "        const gHex = (h) => h.match(/../g).map((x) => parseInt(x, 16)), gEq = (o, h) => h.match(/../g).every((b, i) => game[o + i] === parseInt(b, 16));",
         f'        if (gEq({TAB:#x}, "{H(orig)}")) {{',
         f"          if (game.length < {TAB_B + 0x1000:#x}) {{ const g2 = new Uint8Array({TAB_B + 0x1000:#x}); g2.set(game); game = g2; }}",
         f'          game.set(gHex("{H(new)}"), {TAB:#x});',
         f'          game.set(gHex("{H(cool)}"), {TAB_B:#x});']
for a, e, ent, ptr, old in tset:
    lines.append(f'          if (gEq({ent:#x}, "{old}")) {{ game.set(gHex("{e}"), {a:#x}); game.set(gHex("{ptr}"), {ent:#x}); }}')
lines += ["          window.__gsTabB = true;", "        }", "      }"]
rep("      window.__turn16 = true;\n", "\n".join(lines) + "\n      window.__turn16 = true;\n")

# skill names and the Skills buttons
rep('["Sword of Power", "Lightstrike", "Shield", "Blinding Aura", "Summon Gwaihir"]', '["Lightning Blade", "Lightstrike", "Shield", "Blinding Aura", "Summon Gwaihir"]')
rep("3: { 0: [8, 8] }", "3: { 0: [10, 0] }")
rep("const cdOf = (v) => ", "const cdOf0 = (v) => ")
rep("        const btns = skIcons.map((el) => [el.parentElement, el.classList.contains(\"show\") ? cdOf(el.__v) : null])",
    "        let lbLeft = 0; try { lbLeft = window.__lbLeft ? window.__lbLeft() : 0; } catch (e) {}\n"
    "        const cdOf = (v) => v && v[0] === 3 && v[1] === 0 && lbLeft > 0 ? [lbLeft, 20] : cdOf0(v);   // Lightning Blade cooldown (v204)\n"
    "        const btns = skIcons.map((el) => [el.parentElement, el.classList.contains(\"show\") ? cdOf(el.__v) : null])")
rep("if ((h[P + 0x16A + s] << 24 >> 24) > 0 && !slots.includes(s) && !(xCast && xCast.skill === s)) list.push([hero, s]);",
    "if ((h[P + 0x16A + s] << 24 >> 24) > 0 && !slots.includes(s) && !(hero === 3 && s === 2) && !(xCast && xCast.skill === s)) list.push([hero, s]);")

# aura: softer light blue as the shield fills, whiter while Lightning Blade is up
rep("uniform vec2 AuraP; uniform float AuraK;", "uniform vec2 AuraP; uniform float AuraK; uniform float AuraB, AuraW;", 2)
rep("vec3 ac = vec3(0.72, 0.84, 1.0) * a * AuraK", "vec3 ac = mix(mix(vec3(0.72, 0.84, 1.0), vec3(0.5, 0.78, 1.0), AuraB), vec3(1.0), 0.45 * AuraW) * a * AuraK * (1.0 + 0.3 * AuraB)", 2)
n = s.count("if (fu.AuraK) gl.uniform1f(fu.AuraK, auraK > 0.01 ? auraK : 0);")
assert n >= 1, n
s = s.replace("if (fu.AuraK) gl.uniform1f(fu.AuraK, auraK > 0.01 ? auraK : 0);",
              "if (fu.AuraK) gl.uniform1f(fu.AuraK, auraK > 0.01 ? auraK : 0); if (fu.AuraB) gl.uniform1f(fu.AuraB, window.__shieldFrac || 0); if (fu.AuraW) gl.uniform1f(fu.AuraW, window.__lbGlow || 0);")

# the page script: after impact-fx (it wraps window.__fxView)
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
anchor = "    FX.advance = (dt) => { step(dt); render(dt); };\n    requestAnimationFrame(frame);\n  })();\n"
rep(anchor, anchor + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n")
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s), "aura sites", n)
