# Play Room v194: move the feel wrapper (tools/feel/feel.bin) from ROM 0x1400000 (past 16 MB; the 2-player/online
# link engine crashed on it) to 0x8A000 (freed German bank) and use it in every engine.
# Usage: python3 feel-v194.py in.html(v193) out.html tools/feel/feel.bin
import re, sys
src, dst, feel = sys.argv[1:4]
s = open(src).read(); f = open(feel, 'rb').read().hex()
m = re.search(r'const FEEL = hexBytes\("([0-9a-f]*)"\)', s); s = s[:m.start(1)] + f + s[m.end(1):]
rep = [("// v191-192 movement feel and hobbit leg speed (tools/feel/feel.c): the hero's update wrapper at ROM 0x1400000 (CPU 0x09400000), past the enemy pictures.",
        "// v191-194 movement feel and hobbit leg speed (tools/feel/feel.c): the hero's update wrapper at ROM 0x8A000 (CPU 0x0808A000, the freed German text bank; v194 moved it inside 16 MB so the 2-player/online engine has it too)."),
       (", 0x1400000 + FEEL.length)", ")"),
       ("g.set(FEEL, 0x1400000);", "g.set(FEEL, 0x8A000);"),
       ("const FREE_HOOK = 0x09400001 /* v191: tools/feel hero_feel, which runs 0x0809F001 first */",
        "const FREE_HOOK = 0x0808A001 /* v194: tools/feel hero_feel at ROM 0x8A000, which runs 0x0809F001 first */"),
       ("const hk = M._rotk_link_on ? 0x0809F001 : FREE_HOOK;   // v193: the link engine (P2, online) has only the first 16 MB, and the feel hook lives at 0x09400000\n        if (cur === FREE_GAME || (cur === FREE_HOOK && hk !== FREE_HOOK)) dv.setUint32(at, hk, true);",
        "if (cur === FREE_GAME || cur === 0x09400001 || cur === 0x0809F001) dv.setUint32(at, FREE_HOOK, true);   // v194: one hook for every engine (0x09400001 was v191-v193)"),
       ("const HERO = new Set([0x080236b9, 0x0809f001, 0x09400001]);", "const HERO = new Set([0x080236b9, 0x0809f001, 0x09400001, 0x0808a001]);")]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(dst, 'w').write(s)
