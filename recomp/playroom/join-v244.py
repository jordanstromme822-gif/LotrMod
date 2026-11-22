"""Play Room v244: Flooded Field and Tower Base joined into one map (level slot 51), built by tools/join.

python3 recomp/playroom/join-v244.py IN.html JOIN_DIR OUT.html

JOIN_DIR is the output of tools/join/level.py (join.bin for ROM 0x1700000 = CPU 0x09700000, tables.bin).
Needs the big-map engine (bigmap-v243.py): the maps stay in ROM and the engine swaps the two tile sets.
"""
import base64, json, struct, sys

src, jdir, dst = sys.argv[1:4]
html = open(src, encoding='utf-8').read()
info = json.load(open(jdir + '/join.json'))
assert info['base'] == 0x1700000
data = open(jdir + '/join.bin', 'rb').read()
tables = open(jdir + '/tables.bin', 'rb').read()
lv_at = struct.unpack('<I', tables[:4])[0]; lv = tables[4:4 + 0x4C]
ob_at = struct.unpack('<I', tables[0x50:0x54])[0]; ob = tables[0x54:0x60]


def once(old, new):
    global html
    assert html.count(old) == 1, (html.count(old), old[:80])
    html = html.replace(old, new)


once("const g = new Uint8Array(Math.max(0x1500000 + SIEGE.length,",
     "const JOIN = Uint8Array.from(atob(\"" + base64.b64encode(data).decode() + "\"), (c) => c.charCodeAt(0));\n"
     "        const g = new Uint8Array(Math.max(0x1700000 + JOIN.length, 0x1500000 + SIEGE.length,")
once("g.set(SIEGE, 0x1500000);",
     "g.set(SIEGE, 0x1500000);\n"
     "        // v244 one map: Flooded Field + Tower Base joined at the 3D World layout (tools/join), in Flooded Field's slot 51.\n"
     "        // Starts with the BMAP table the engine reads to swap tile sets in the middle.\n"
     "        g.set(JOIN, 0x1700000);\n"
     "        g.set(hexBytes(\"" + lv.hex() + "\"), 0x%X);\n" % lv_at +
     "        g.set(hexBytes(\"" + ob.hex() + "\"), 0x%X);" % ob_at)
open(dst, 'w', encoding='utf-8').write(html)
print('ok', len(html), 'join bytes', len(data))
