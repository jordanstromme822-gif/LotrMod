#!/usr/bin/env python3
"""Play Room: load the faster 2-player engine (2026-11-11, recomp/link/link-speed.patch).

  python3 link-speed-v169.py in.html out.html

The 2-player engine (wide/rotk-link*) is now about 35 MB, more than two artifact files can hold, so it ships in
three parts (rotk-link-0/1/2.wasm). Both places that load it (the P2 helper's fetchEngine and the online game)
fetch the parts and join them. The 1-player engine keeps its two parts. Link files get ?v=169 so a phone never
mixes an old .js with new .wasm.
"""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def sub1(pat, rep, flags=0):
    global s
    n = len(re.findall(pat, s, flags))
    assert n == 1, (pat[:60], n)
    s = re.sub(pat, rep, s, flags=flags)

# P2 helper / local engines
sub1(r'const V = isLink \? "\?v=\d+" : "(\?v=\d+)";', r'const V = isLink ? "?v=169" : "\1";   // v169 link: faster 2-player engine in 3 parts (2026-11-11);')
old = '''      const [w0, w1, toml] = await Promise.all([fetchBin(eng + "-0.wasm" + V), fetchBin(eng + "-1.wasm" + V), fetch(isLink ? "wide/game-link.txt" : "wide/game.txt").then((r) => r.text())]);
      const wasm = new Uint8Array(w0.length + w1.length); wasm.set(w0); wasm.set(w1, w0.length);'''
new = '''      const nParts = isLink ? 3 : 2;   // the 2-player engine is too big for two artifact files (v169)
      const [parts, toml] = await Promise.all([Promise.all(Array.from({ length: nParts }, (_, i) => fetchBin(eng + "-" + i + ".wasm" + V))), fetch(isLink ? "wide/game-link.txt" : "wide/game.txt").then((r) => r.text())]);
      const wasm = new Uint8Array(parts.reduce((n, p) => n + p.length, 0)); { let o = 0; for (const p of parts) { wasm.set(p, o); o += p.length; } }'''
assert s.count(old) == 1; s = s.replace(old, new)

# online game
i = s.index('if (!window.createRotkLink) await new Promise((res, rej) => { const sc = document.createElement("script"); sc.src = "wide/rotk-link.js" + V;')
j = s.rindex('const V = "?v=', 0, i)
assert i - j < 400, i - j
k = s.index('";', j)
s = s[:j] + 'const V = "?v=169' + s[k:]
old = '''      const [w0, w1, toml, bios] = await Promise.all([fetchBin("wide/rotk-link-0.wasm" + V), fetchBin("wide/rotk-link-1.wasm" + V), fetch("wide/game-link.txt").then((r) => r.text()), fetch("wide/bios.txt").then((r) => r.text()).then((t) => unb64(t.trim()))]);
      const wasm = new Uint8Array(w0.length + w1.length); wasm.set(w0); wasm.set(w1, w0.length);'''
new = '''      const [parts, toml, bios] = await Promise.all([Promise.all([0, 1, 2].map((i) => fetchBin("wide/rotk-link-" + i + ".wasm" + V))), fetch("wide/game-link.txt").then((r) => r.text()), fetch("wide/bios.txt").then((r) => r.text()).then((t) => unb64(t.trim()))]);
      const wasm = new Uint8Array(parts.reduce((n, p) => n + p.length, 0)); { let o = 0; for (const p of parts) { wasm.set(p, o); o += p.length; } }'''
assert s.count(old) == 1; s = s.replace(old, new)
open(dst, "w", encoding="utf-8").write(s)
print("ok")
