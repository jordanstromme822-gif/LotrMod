"""Play Room: rebuild Isengard's mountains on a page that already has the v255 layer (recomp/playroom/mountains-v255.py).

python3 recomp/playroom/mountains-update.py IN.html PACK_DIR MTN_DIR OUT_DIR V

Swaps the region data for PACK_DIR's (region-v249.py), refreshes the layer's config from MTN_DIR/mountains.json, bumps
the layer's files and the 3D World picture (maps/x/R51.webp) to ?v=V and copies the layer's files into OUT_DIR/maps/x/.
"""
import json, os, re, shutil, subprocess, sys
src, pdir, mdir, odir, V = sys.argv[1:6]; V = int(V)
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(odir, 'maps', 'x'), exist_ok=True)
tmp = os.path.join(odir, '.region.html')
subprocess.check_call([sys.executable, os.path.join(HERE, 'region-v249.py'), src, pdir, tmp])
html = open(tmp, encoding='utf-8').read(); os.remove(tmp)
info = json.load(open(os.path.join(mdir, 'mountains.json')))
cfg = dict(bin='maps/x/M51data.wasm?v=%d' % V, rock='maps/x/M51r.png?v=%d' % V, ground='maps/x/M51g.png?v=%d' % V,
           nRock=info['rock'], nGround=info['ground'], rows=info['ground_rows'], key=info['key'], shade=info['shade'], level=51)
pat = re.compile(r'const O = \{"bin":"maps/x/M51data\.wasm[^\n]*?\};')
assert len(pat.findall(html)) == 1
html = pat.sub(lambda m: 'const O = ' + json.dumps(cfg, separators=(',', ':')) + ';', html, 1)
pat = re.compile(r'src: "maps/x/R51\.webp\?v=\d+"')
assert len(pat.findall(html)) == 1
html = pat.sub('src: "maps/x/R51.webp?v=%d"' % V, html, 1)
open(os.path.join(odir, 'index.html'), 'w', encoding='utf-8').write(html)
for a, b in (('mountains.bin', 'M51data.wasm'), ('mountains-rock.png', 'M51r.png'), ('mountains-ground.png', 'M51g.png')):
    shutil.copy(os.path.join(mdir, a), os.path.join(odir, 'maps', 'x', b))
print('ok', len(html))
