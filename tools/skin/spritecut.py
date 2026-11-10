# Sprite skin tiles: rebuild each OAM sprite from VRAM (no background), upscale 4x as a sheet, cut 8x8 tiles.
# Usage: spritecut.py model.pth OUTDIR capdir...   (writes OUTDIR/sprites.npz: key -> 32x32 RGBA)
import sys, glob, json, os, numpy as np, torch
from PIL import Image
from spandrel import ModelLoader
SIZES = {0: [(8,8),(16,16),(32,32),(64,64)], 1: [(16,8),(32,8),(32,16),(64,32)], 2: [(8,16),(8,32),(16,32),(32,64)]}
def fnv(b):
    h = 0x811c9dc5
    for x in b: h = ((h ^ x) * 0x01000193) & 0xffffffff
    return h
def tile_idx(tb, c256):
    a = np.frombuffer(tb, np.uint8)
    if c256: return a.reshape(8, 8).astype(int)
    lo, hi = a & 15, a >> 4
    return np.stack([lo, hi], 1).reshape(8, 8).astype(int)
model = ModelLoader().load_from_file(sys.argv[1]).eval()
out = sys.argv[2]; sprites = {}
for cap in sys.argv[3:]:
    for jf in sorted(glob.glob(cap + '/*.json')):
        n = jf[:-5]
        if not os.path.exists(n + '.oam'): continue
        vram = open(n + '.vram', 'rb').read(); pal = open(n + '.pal', 'rb').read(); oam = open(n + '.oam', 'rb').read()
        for i in range(128):
            a0, a1, a2 = [int.from_bytes(oam[i*8+k:i*8+k+2], 'little') for k in (0, 2, 4)]
            if a0 & 0x100 or a0 & 0x200: continue           # affine or hidden
            shape, size = a0 >> 14, a1 >> 14
            if shape == 3: continue
            w, h = SIZES[shape][size]; c256 = (a0 >> 13) & 1; tile = a2 & 0x3ff; bank = a2 >> 12
            tw, th = w // 8, h // 8
            keys = []; img = np.zeros((h, w, 3), np.uint8); mask = np.zeros((h, w), bool)
            pb = pal[0x200:0x400] if c256 else pal[0x200 + bank*32: 0x200 + bank*32 + 32]
            colors = np.array([[(c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3] for c in np.frombuffer(pb, '<u2')], np.uint8)
            for ty in range(th):
                for tx in range(tw):
                    t = tile + (ty * tw + tx) * (2 if c256 else 1)
                    off = 0x10000 + t * 32; tb = vram[off: off + (64 if c256 else 32)]
                    idx = tile_idx(tb, c256)
                    img[ty*8:ty*8+8, tx*8:tx*8+8] = colors[idx]; mask[ty*8:ty*8+8, tx*8:tx*8+8] = idx != 0
                    keys.append((tx, ty, '%08x%08x%d' % (fnv(tb), fnv(pb), c256), idx != 0))
            if mask.sum() < 6: continue
            sk = tuple(k for _, _, k, _ in keys)
            if sk in sprites: continue
            sprites[sk] = (img, mask, keys)
print('unique sprites', len(sprites), flush=True)
# fill transparent pixels with nearest opaque colour so the upscaler sees no fake background
def dilate(img, mask):
    img = img.astype(np.float32).copy(); m = mask.copy()
    for _ in range(64):
        if m.all(): break
        acc = np.zeros_like(img); cnt = np.zeros(m.shape, np.float32)
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            sm = np.roll(m, (dy, dx), (0, 1)); si = np.roll(img, (dy, dx), (0, 1))
            acc += si * sm[..., None]; cnt += sm
        new = (~m) & (cnt > 0)
        img[new] = acc[new] / cnt[new][:, None]; m = m | new
    return img
tiles = {}
for sk, (img, mask, keys) in sprites.items():
    h, w = mask.shape; P = 8
    src = np.pad(dilate(img, mask), ((P, P), (P, P), (0, 0)), mode='edge') / 255
    t = torch.from_numpy(src).permute(2, 0, 1)[None].float()
    with torch.no_grad(): o = model(t)[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255
    o = o[P*4:P*4+h*4, P*4:P*4+w*4]
    m4 = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((w*4, h*4), Image.BILINEAR)).astype(np.float32)
    al = np.clip((m4 - 64) * 255 / 128, 0, 255)
    for tx, ty, k, op in keys:
        if not op.any(): continue
        cell = np.dstack([o[ty*32:ty*32+32, tx*32:tx*32+32], al[ty*32:ty*32+32, tx*32:tx*32+32]])
        e = tiles.setdefault(k, [np.zeros((32, 32, 4), np.float32), 0]); e[0] += cell; e[1] += 1
os.makedirs(out, exist_ok=True)
np.savez_compressed(out + '/sprites.npz', **{k: (v[0] / v[1]).clip(0, 255).astype(np.uint8) for k, v in tiles.items()})
print('sprite tiles', len(tiles))
