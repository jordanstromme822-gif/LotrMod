"""Play Room v255: Isengard's mountains (tools/region/mountains.py) around the region, drawn by the page behind the heroes.

python3 recomp/playroom/mountains-v255.py IN.html PACK_DIR MTN_DIR OUT_DIR

Swaps the region data for PACK_DIR's (tools/region/pack.py of the mountains' region.pkl, as region-v249.py does), adds
recomp/playroom/mountain-layer.js (drawn before Orthanc's horns), and writes OUT_DIR/index.html plus the layer's files
OUT_DIR/maps/x/M51data.wasm (zlib bytes; named .wasm only so the artifact host serves it), M51r.png, M51g.png. The 3D World picture (maps/x/R51.webp) goes up to ?v=255.
"""
import json, os, shutil, subprocess, sys
src, pdir, mdir, odir = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(odir, 'maps', 'x'), exist_ok=True)
tmp = os.path.join(odir, '.region.html')
subprocess.check_call([sys.executable, os.path.join(HERE, 'region-v249.py'), src, pdir, tmp])
html = open(tmp, encoding='utf-8').read(); os.remove(tmp)
info = json.load(open(os.path.join(mdir, 'mountains.json')))
V = 255
cfg = dict(bin='maps/x/M51data.wasm?v=%d' % V, rock='maps/x/M51r.png?v=%d' % V, ground='maps/x/M51g.png?v=%d' % V,
           nRock=info['rock'], nGround=info['ground'], rows=info['ground_rows'], key=info['key'], shade=info['shade'], level=51)
js = open(os.path.join(HERE, 'mountain-layer.js'), encoding='utf-8').read().replace('__MOUNTAINS__', json.dumps(cfg, separators=(',', ':')))
anchor = "  // v247 Orthanc's four horns (tools/region/orthanc)"
assert html.count(anchor) == 1
html = html.replace(anchor, js + anchor, 1)
call = "        if (window.__orthanc) try { window.__orthanc(src8, srcOff, w, h); } catch (e) {}"
assert html.count(call) == 1
html = html.replace(call, "        if (window.__mountains) try { window.__mountains(src8, srcOff, w, h); } catch (e) {}   // v255: Isengard's mountains behind the heroes\n" + call, 1)
old = 'src: "maps/x/R51.webp?v=254"'
assert html.count(old) == 1
html = html.replace(old, 'src: "maps/x/R51.webp?v=%d"' % V, 1)
open(os.path.join(odir, 'index.html'), 'w', encoding='utf-8').write(html)
for a, b in (('mountains.bin', 'M51data.wasm'), ('mountains-rock.png', 'M51r.png'), ('mountains-ground.png', 'M51g.png')):
    shutil.copy(os.path.join(mdir, a), os.path.join(odir, 'maps', 'x', b))
print('ok', len(html))
