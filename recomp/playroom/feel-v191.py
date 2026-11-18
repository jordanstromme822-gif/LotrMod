# Play Room v191: movement feel wrapper (tools/feel/feel.bin at ROM 0x1400000), hero update -> 0x09400001.
# Usage: python3 feel-v191.py in.html out.html tools/feel/feel.bin
import sys
src,dst,feel=sys.argv[1:4]
s=open(src).read(); f=open(feel,'rb').read().hex()
a="const g = new Uint8Array(Math.max(0x1000000 + H16.length, 0x1080000 + (E16 ? E16.length : 4))); g.set(game.subarray(0, 0x1000000)); g.set(H16, 0x1000000);\n        if (E16) g.set(E16, 0x1080000);"
assert s.count(a)==1
b=("// v191 movement feel (tools/feel/feel.c): the hero's update wrapper at ROM 0x1400000 (CPU 0x09400000), past the enemy pictures.\n"
   "        const FEEL = hexBytes(\""+f+"\");\n"
   "        const g = new Uint8Array(Math.max(0x1000000 + H16.length, 0x1080000 + (E16 ? E16.length : 4), 0x1400000 + FEEL.length)); g.set(game.subarray(0, 0x1000000)); g.set(H16, 0x1000000);\n"
   "        if (E16) g.set(E16, 0x1080000);\n        g.set(FEEL, 0x1400000);")
s=s.replace(a,b)
a="const FREE_HOOK = 0x0809F001, FREE_GAME = 0x080236B9"
assert s.count(a)==1
s=s.replace(a,"const FREE_HOOK = 0x09400001 /* v191: tools/feel hero_feel, which runs 0x0809F001 first */, FREE_GAME = 0x080236B9")
a="const HERO = new Set([0x080236b9, 0x0809f001]);"
assert s.count(a)==1
s=s.replace(a,"const HERO = new Set([0x080236b9, 0x0809f001, 0x09400001]);")
open(dst,'w').write(s)
