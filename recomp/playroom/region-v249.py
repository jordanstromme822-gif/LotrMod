"""Play Room v249: the Isengard region with the Ring of Isengard (tools/region/ring.py) and its broken Gate.

python3 recomp/playroom/region-v249.py IN.html PACK_DIR OUT.html

Swaps the region data v247 put in (REGION at ROM 0x1C80000) and the slot's level and object table entries for a new
tools/region/pack.py output. Nothing else changes: same engine (?v=247), same Orthanc layer.
"""
import base64, json, re, struct, sys
src, pdir, dst = sys.argv[1:4]
html = open(src, encoding='utf-8').read()
info = json.load(open(pdir + '/region.json'))
assert info['base'] == 0x1C80000
data = open(pdir + '/region.bin', 'rb').read()
tables = open(pdir + '/tables.bin', 'rb').read()
lv_at = struct.unpack('<I', tables[:4])[0]; lv = tables[4:4 + 0x4C]
ob_at = struct.unpack('<I', tables[0x50:0x54])[0]; ob = tables[0x54:0x60]
assert 0x1C80000 + len(data) <= 0x2000000 and lv_at == 0x6A97C and ob_at == 0x6C354

i = html.index('const REGION = Uint8Array.from(atob("') + len('const REGION = Uint8Array.from(atob("')
j = html.index('"), (c) => c.charCodeAt(0));', i)
html = html[:i] + base64.b64encode(data).decode() + html[j:]
for at, b in ((lv_at, lv), (ob_at, ob)):
    pat = r'g\.set\(hexBytes\("([0-9a-f]+)"\), 0x%X\);' % at
    assert len(re.findall(pat, html)) == 1, hex(at)
    html = re.sub(pat, 'g.set(hexBytes("%s"), 0x%X);' % (b.hex(), at), html)
html = html.replace("        // v247 Isengard region (tools/region):", "        // v247 Isengard region (tools/region; v249: with the Ring of Isengard and its broken Gate):", 1)
open(dst, 'w', encoding='utf-8').write(html)
print('ok', len(html), 'region bytes', len(data))
