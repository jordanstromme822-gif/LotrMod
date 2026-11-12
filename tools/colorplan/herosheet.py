"""Hero tile sheets for hand redraws (private: these are the game's own pixels; never commit the output).

usage: herosheet.py outdir name:capdump [...]
Per hero: <name>-tiles.png = every unique 8x8 hero tile at 2x (16x16 cells, 1 px gap, 32 per row, original colours,
transparent where the game pixel is empty), <name>-tiles.json = [{key, col, row, bank}] with the same FNV key as
tools/skin/cut.py / spritecut.py (so tools/redraw/pack.py can pack a 16x16 redraw per key), and <name>-poses.png =
each captured pose at 2x for reference."""
import sys, os, json, numpy as np
from PIL import Image
from herocut import pieces, hero_pieces, REC
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for a in sys.argv[2:]:
    name, path = a.split(':', 1); D = open(path, 'rb').read()
    tiles = {}; poses = []; seen = set()
    for o in range(0, len(D) - REC + 1, REC):
        hp = hero_pieces(pieces(D[o:o+REC]))
        if not hp: continue
        sig = tuple(sorted((p['x'], p['y'], p['hf'], p['vf'], tuple(k for _, _, k in p['keys'])) for p in hp))
        if sig in seen: continue
        seen.add(sig)
        x0 = min(p['x'] for p in hp); y0 = min(p['y'] for p in hp)
        W = max(p['x'] + p['w'] for p in hp) - x0; H = max(p['y'] + p['h'] for p in hp) - y0
        pic = np.zeros((H, W, 4), np.uint8)
        for p in sorted(hp, key=lambda p: -p['i']):
            rgba = np.zeros((p['h'], p['w'], 4), np.uint8)
            for c in range(1, 16): rgba[p['img'] == c] = list(p['pal'][c]) + [255]
            for tx, ty, k in p['keys']:
                if k not in tiles and rgba[ty*8:ty*8+8, tx*8:tx*8+8, 3].any():
                    tiles[k] = (rgba[ty*8:ty*8+8, tx*8:tx*8+8].copy(), p['bank'])
            if p['hf']: rgba = rgba[:, ::-1]
            if p['vf']: rgba = rgba[::-1]
            sub = pic[p['y']-y0:p['y']-y0+p['h'], p['x']-x0:p['x']-x0+p['w']]
            m = rgba[..., 3] > 0; sub[m] = rgba[m]
        poses.append(pic)
    keys = list(tiles); PER = 32; rows = (len(keys) + PER - 1) // PER
    sheet = np.zeros((rows * 17, PER * 17, 4), np.uint8); meta = []
    for i, k in enumerate(keys):
        r, c = divmod(i, PER); t, bank = tiles[k]
        sheet[r*17:r*17+16, c*17:c*17+16] = t.repeat(2, 0).repeat(2, 1)
        meta.append({'key': k, 'col': c, 'row': r, 'bank': bank})
    Image.fromarray(sheet).save(f'{out}/{name}-tiles.png')
    json.dump({'cell': 16, 'gap': 1, 'per_row': PER, 'tiles': meta}, open(f'{out}/{name}-tiles.json', 'w'))
    PW = 72; per = 16; prow = (len(poses) + per - 1) // per
    ps = np.zeros((prow * PW * 2, per * PW * 2, 4), np.uint8)
    for i, p in enumerate(poses):
        r, c = divmod(i, per); p2 = p.repeat(2, 0).repeat(2, 1)[:PW*2, :PW*2]
        ps[r*PW*2:r*PW*2+p2.shape[0], c*PW*2:c*PW*2+p2.shape[1]] = p2
    Image.fromarray(ps).save(f'{out}/{name}-poses.png')
    print(name, 'tiles', len(keys), 'poses', len(poses), flush=True)
