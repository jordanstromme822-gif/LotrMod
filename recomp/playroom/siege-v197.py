"""Play Room v197: Siege map (Helm's Deep, both halves in one map, open ground north of the wall).

python3 recomp/playroom/siege-v197.py IN.html SIEGE_DIR OUT.html

SIEGE_DIR is the output of tools/siege/build.py ROM SIEGE_DIR --base 0x1500000
(siege.bin, tables.bin, siege.json). The page puts siege.bin at ROM 0x1500000
(CPU 0x09500000, past the movement-feel code at 0x1400000) and points level slot 45
(an unused Hornburg slot) at it; the Levels list gets a Siege entry, which uses the
same warp as every other level, so it works in 1-player, P2 and online games.
"""
import base64, json, struct, sys

src, sdir, dst = sys.argv[1:4]
html = open(src, encoding='utf-8').read()
info = json.load(open(sdir + '/siege.json'))
assert info['base'] == 0x1500000, 'build with --base 0x1500000'
data = open(sdir + '/siege.bin', 'rb').read()
tables = open(sdir + '/tables.bin', 'rb').read()
lv_at = struct.unpack('<I', tables[:4])[0]; lv = tables[4:4 + 0x4C]
ob_at = struct.unpack('<I', tables[0x50:0x54])[0]; ob = tables[0x54:0x60]


def once(old, new):
    global html
    assert html.count(old) == 1, (html.count(old), old[:80])
    html = html.replace(old, new)


# 1) ROM: the map data past 16 MB, level slot 45 and its spawn table entry pointed at it
once("const g = new Uint8Array(Math.max(0x1000000 + H16.length,",
     "const SIEGE = Uint8Array.from(atob(\"" + base64.b64encode(data).decode() + "\"), (c) => c.charCodeAt(0));\n"
     "        const g = new Uint8Array(Math.max(0x1500000 + SIEGE.length, 0x1000000 + H16.length,")
once("g.set(FEEL, 0x1400000);",
     "g.set(FEEL, 0x1400000);\n"
     "        // v197 Siege map (tools/siege/build.py): Hornburg + Hornburg Valley joined and extended north, no enemies,\n"
     "        // in level slot 45 (unused). Layout data only: the pictures come from the game's own Hornburg tiles.\n"
     "        g.set(SIEGE, 0x1500000);\n"
     "        g.set(hexBytes(\"" + lv.hex() + "\"), 0x%X);\n" % lv_at +
     "        g.set(hexBytes(\"" + ob.hex() + "\"), 0x%X);" % ob_at)

# 2) Levels list: a Siege group
once('["Bonus levels", [[82, "Moria"], [121, "Amon Sul"], [46, "Hornburg"], [37, "Entwood"]]],',
     '["Bonus levels", [[82, "Moria"], [121, "Amon Sul"], [46, "Hornburg"], [37, "Entwood"]]],\n'
     '    ["Siege", [[45, "Helm\'s Deep (whole wall, no enemies yet)"]]],')
once('list.forEach(([lv, name], i) => add((group === "Bonus levels" ? "" : (i + 1) + ". ") + name',
     'list.forEach(([lv, name], i) => add((group === "Bonus levels" || group === "Siege" ? "" : (i + 1) + ". ") + name')

open(dst, 'w', encoding='utf-8').write(html)
print('ok', len(html), 'siege bytes', len(data))
