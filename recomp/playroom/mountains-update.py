"""Play Room: rebuild Isengard's mountains on a page that already has the v255 layer (recomp/playroom/mountains-v255.py).

python3 recomp/playroom/mountains-update.py IN.html PACK_DIR MTN_DIR OUT_DIR V [DROP_DIR]

Swaps the region data for PACK_DIR's (region-v249.py), puts in the current recomp/playroom/mountain-layer.js with its
config from MTN_DIR/mountains.json, bumps the layer's files and the 3D World picture (maps/x/R51.webp) to ?v=V and copies
the layer's files into OUT_DIR/maps/x/. DROP_DIR (tools/region/drop.py, water.py) adds the far valley's pictures (M51p.png, M51f.png) and the flood water (M51w.png).
"""
import json, os, re, shutil, subprocess, sys
src, pdir, mdir, odir, V = sys.argv[1:6]; V = int(V); ddir = sys.argv[6] if len(sys.argv) > 6 else None
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(odir, 'maps', 'x'), exist_ok=True)
tmp = os.path.join(odir, '.region.html')
subprocess.check_call([sys.executable, os.path.join(HERE, 'region-v249.py'), src, pdir, tmp])
html = open(tmp, encoding='utf-8').read(); os.remove(tmp)
info = json.load(open(os.path.join(mdir, 'mountains.json')))
cfg = dict(bin='maps/x/M51data.wasm?v=%d' % V, rock='maps/x/M51r.png?v=%d' % V, ground='maps/x/M51g.png?v=%d' % V,
           nRock=info['rock'], nGround=info['ground'], rows=info['ground_rows'], key=info['key'], shade=info['shade'], level=51)
if ddir:
    cfg.update(plain='maps/x/M51p.png?v=%d' % V, face='maps/x/M51f.png?v=%d' % V, plainY=7400)
    if os.path.exists(os.path.join(ddir, 'water.png')): cfg.update(water='maps/x/M51w.png?v=%d' % V, vents=info.get('vents', []))
js = open(os.path.join(HERE, 'mountain-layer.js'), encoding='utf-8').read().replace('__MOUNTAINS__', json.dumps(cfg, separators=(',', ':')))
a = html.index("  // v255 Isengard's mountains"); b = html.index("  // v247 Orthanc's four horns (tools/region/orthanc)")
assert a < b and html.count("  // v255 Isengard's mountains") == 1
html = html[:a] + js + html[b:]
pat = re.compile(r'src: "maps/x/R51\.webp\?v=\d+"')
assert len(pat.findall(html)) == 1
html = pat.sub('src: "maps/x/R51.webp?v=%d"' % V, html, 1)
open(os.path.join(odir, 'index.html'), 'w', encoding='utf-8').write(html)
for a, b in (('mountains.bin', 'M51data.wasm'), ('mountains-rock.png', 'M51r.png'), ('mountains-ground.png', 'M51g.png')):
    shutil.copy(os.path.join(mdir, a), os.path.join(odir, 'maps', 'x', b))
if ddir:
    for a, b in (('drop-plain.png', 'M51p.png'), ('drop-face.png', 'M51f.png'), ('water.png', 'M51w.png')):
        shutil.copy(os.path.join(ddir, a), os.path.join(odir, 'maps', 'x', b))
print('ok', len(html))
