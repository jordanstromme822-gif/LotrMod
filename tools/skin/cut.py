# Cut skin tiles from captured frames + their 4x upscales. Usage: cut.py OUTDIR capdir...
import sys, json, glob, os, numpy as np
from PIL import Image
def fnv(b):
    h = 0x811c9dc5
    for x in b: h = ((h ^ x) * 0x01000193) & 0xffffffff
    return h
out = sys.argv[1]; acc = {}
for cap in sys.argv[2:]:
    for jf in sorted(glob.glob(cap + '/*.json')):
        n = jf[:-5]
        if not os.path.exists(n + '_x4.png'): continue
        j = json.load(open(jf)); w, h = j['w'], j['h']
        tags = np.frombuffer(open(n + '.tags', 'rb').read(), dtype='<u4').reshape(h, w)
        vram = open(n + '.vram', 'rb').read(); pal = open(n + '.pal', 'rb').read()
        big = np.asarray(Image.open(n + '_x4.png').convert('RGB')).astype(np.float32)
        inst = {}
        ys, xs = np.nonzero(tags >> 31)
        for y, x in zip(ys, xs):
            t = int(tags[y, x]); tx = (t >> 17) & 7; ty = (t >> 20) & 7; hf = (t >> 23) & 1; vf = (t >> 24) & 1
            ox = x - (7 - tx if hf else tx); oy = y - (7 - ty if vf else ty)
            k = (ox, oy, t & 0x3ffffff & ~(0x3f << 17))
            e = inst.setdefault(k, [0, 0]); e[0] += 1
            if t & (3 << 26): e[1] += 1
        for (ox, oy, base), (cnt, bl) in inst.items():
            if bl or ox < 0 or oy < 0 or ox + 8 > w or oy + 8 > h: continue
            slot = base & 0xfff; bank = (base >> 12) & 15; c256 = (base >> 16) & 1; hf = (base >> 23) & 1; vf = (base >> 24) & 1; obj = (base >> 25) & 1
            tb = vram[slot * 32: slot * 32 + (64 if c256 else 32)]
            if len(tb) < (64 if c256 else 32): continue
            idx = np.zeros((8, 8), int)
            for py in range(8):
                for px in range(8):
                    idx[py, px] = tb[py * 8 + px] if c256 else ((tb[py * 4 + px // 2] >> 4) if px & 1 else (tb[py * 4 + px // 2] & 15))
            opaque = idx != 0
            if cnt != int(opaque.sum()) or cnt == 0: continue   # some texel covered by something in front
            pb = pal[(0x200 if obj else 0):][:512] if c256 else pal[(0x200 if obj else 0) + bank * 32:][:32]
            key = '%08x%08x%d' % (fnv(tb), fnv(pb), c256)
            crop = big[oy * 4: oy * 4 + 32, ox * 4: ox * 4 + 32]
            if hf: crop = crop[:, ::-1]
            if vf: crop = crop[::-1]
            a = acc.setdefault(key, [np.zeros((32, 32, 3), np.float32), 0, opaque, obj])
            a[0] += crop; a[1] += 1
        print(n, len(acc), flush=True)
keys = sorted(acc); C = 36; PER = 112
rows = (len(keys) + PER - 1) // PER
atlas = np.zeros((rows * C, PER * C, 4), np.uint8)
for i, k in enumerate(keys):
    s, c, op, obj = acc[k]; rgb = s / c
    m = Image.fromarray((op * 255).astype(np.uint8)).resize((32, 32), Image.BILINEAR)
    al = np.asarray(m).astype(np.float32)
    al = np.clip((al - 64) * 255 / 128, 0, 255) if not op.all() else np.full((32, 32), 255, np.float32)
    cell = np.dstack([rgb, al]).clip(0, 255).astype(np.uint8)
    cell = np.pad(cell, ((2, 2), (2, 2), (0, 0)), mode='edge')
    r, cc = divmod(i, PER); atlas[r * C:(r + 1) * C, cc * C:(cc + 1) * C] = cell
os.makedirs(out, exist_ok=True)
Image.fromarray(atlas, 'RGBA').save(out + '/atlas.png', optimize=True)
json.dump({'cell': C, 'per': PER, 'keys': keys}, open(out + '/map.json', 'w'))
print('tiles', len(keys), 'atlas', atlas.shape)
