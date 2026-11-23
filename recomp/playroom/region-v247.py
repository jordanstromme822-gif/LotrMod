"""Play Room v247: the Isengard region (Campsite, Flooded Field, Tower Base and the ground between, tools/region) as one
level in slot 51, replacing v244's Flooded Field + Tower Base join. Orthanc's four horns are drawn by the page over the
game's picture (orthanc-layer.js): the hero walks behind them, and they lean a little with the camera for height.

python3 recomp/playroom/region-v247.py IN.html PACK_DIR LAYER_DIR OUT.html

PACK_DIR = tools/region/pack.py output (region.bin for ROM 0x1C80000 = CPU 0x09C80000, tables.bin, region.json).
LAYER_DIR = tools/region/orthanc/layer.py output (layer.json). Engine ?v=247: bigmap.s reads the 'BMP2' zone table.

v244 put its map data at ROM 0x1700000, inside the 32-facing pictures (0x1610000-0x1C22FBC), so part of those pictures
was overwritten; the region now sits past them.
"""
import base64, json, os, re, struct, subprocess, sys

src, pdir, ldir, dst = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
html = open(src, encoding='utf-8').read()
info = json.load(open(pdir + '/region.json'))
assert info['base'] == 0x1C80000
data = open(pdir + '/region.bin', 'rb').read()
tables = open(pdir + '/tables.bin', 'rb').read()
lv_at = struct.unpack('<I', tables[:4])[0]; lv = tables[4:4 + 0x4C]
ob_at = struct.unpack('<I', tables[0x50:0x54])[0]; ob = tables[0x54:0x60]
assert 0x1C80000 + len(data) <= 0x2000000


def once(old, new):
    global html
    assert html.count(old) == 1, (html.count(old), old[:80])
    html = html.replace(old, new)


# region data instead of the v244 join
i = html.index('const JOIN = Uint8Array.from(atob("'); j = html.index('"), (c) => c.charCodeAt(0));', i)
html = html[:i] + 'const REGION = Uint8Array.from(atob("' + base64.b64encode(data).decode() + html[j:]
once("const g = new Uint8Array(Math.max(0x1700000 + JOIN.length,", "const g = new Uint8Array(Math.max(0x1C80000 + REGION.length,")
i = html.index("        // v244 one map: Flooded Field + Tower Base joined"); j = html.index("g.set(JOIN, 0x1700000);", i) + len("g.set(JOIN, 0x1700000);")
html = html[:i] + ("        // v247 Isengard region (tools/region): Campsite, Flooded Field, Tower Base and the ground between as one level in\n"
                   "        // slot 51. Starts with the BMP2 zone table the engine reads to load each zone's tile set. Past the 32-facing\n"
                   "        // pictures (they end at 0x1C22FBC; v244's join at 0x1700000 overwrote part of them).\n"
                   "        g.set(REGION, 0x1C80000);") + html[j:]
m = re.search(r'g\.set\(hexBytes\("([0-9a-f]+)"\), 0x6A97C\);', html); assert m and len(m.group(1)) == 0x98
html = html.replace(m.group(0), 'g.set(hexBytes("%s"), 0x%X);' % (lv.hex(), lv_at)); assert lv_at == 0x6A97C
m = re.search(r'g\.set\(hexBytes\("([0-9a-f]+)"\), 0x6C354\);', html); assert m
html = html.replace(m.group(0), 'g.set(hexBytes("%s"), 0x%X);' % (ob.hex(), ob_at)); assert ob_at == 0x6C354
# big-map code with the zone table (bigmap.s)
js = subprocess.check_output([sys.executable, os.path.join(HERE, '../../tools/bigmap/bigmap.py'), '--js']).decode().rstrip('\n')
i = html.index("      // Big maps read straight from ROM (tools/bigmap)"); j = html.index("BM_NEW.forEach(([o, h]) => game.set(hexBytes(h), o)); }", i) + len("BM_NEW.forEach(([o, h]) => game.set(hexBytes(h), o)); }")
html = html[:i] + js + html[j:]
once('const V = isLink ? "?v=246" : "?v=hd2";', 'const V = isLink ? "?v=247" : "?v=hd2";   // v247: big maps in tile-set zones (BMP2)')

# Orthanc's horns, drawn over the game's picture
lay = json.load(open(ldir + '/layer.json'))
layer_js = open(os.path.join(HERE, 'orthanc-layer.js'), encoding='utf-8').read().replace('__ORTHANC__', json.dumps(lay, separators=(',', ':')))
once("  const WideHost = {", layer_js + "\n  const WideHost = {")
once("        let src8 = this._u8, srcOff = base + this.d.pixels; const nB = w * h * 3;",
     "        let src8 = this._u8, srcOff = base + this.d.pixels; const nB = w * h * 3;\n"
     "        if (window.__orthanc) try { window.__orthanc(src8, srcOff, w, h); } catch (e) {}   // v247: Orthanc's horns over the picture")
open(dst, 'w', encoding='utf-8').write(html)
print('ok', len(html), 'region bytes', len(data))
