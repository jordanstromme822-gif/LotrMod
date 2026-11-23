from recolor import *
from PIL import Image
LIVE = '/tmp/claude-0/-home-user/972dab79-8ec0-567e-9dbe-b1d16b78ca89/scratchpad/live/maps/L%d.webp'
_al = {}
def aligned(L):
    """live picture + ROM index aligned to it (index -1 where the live pixel isn't from the tile layers)."""
    if L in _al: return _al[L]
    live = np.asarray(Image.open(LIVE % L).convert('RGB')).astype(np.int16)
    idx = load(L).astype(np.int16); ren = rgb(meta[L]['pal'])[idx].astype(np.int16)
    best = None
    for dy in range(0, idx.shape[0] - live.shape[0] + 1):
        for dx in range(0, idx.shape[1] - live.shape[1] + 1):
            r = ren[dy:dy + live.shape[0], dx:dx + live.shape[1]]
            m = (np.abs(r - live).sum(2) < 24).mean()
            if best is None or m > best[0]: best = (m, dy, dx)
    m, dy, dx = best
    I = idx[dy:dy + live.shape[0], dx:dx + live.shape[1]].copy()
    r = ren[dy:dy + live.shape[0], dx:dx + live.shape[1]]
    I[np.abs(r - live).sum(2) >= 24] = -1
    _al[L] = (live.astype(np.uint8), I, m)
    return _al[L]
def new_palette(pal, plan, palp=None):
    """plan: {'banks': {b: rules}, 'default': rules, 'entries': {i: rgb}}"""
    col = rgb(pal); out = col.copy()
    for b in range(16):
        banks = plan.get('banks_by_pal', {}).get(palp, plan.get('banks', {}))
        rules = banks.get(b, plan.get('default', []))
        if rules:
            for r in rules:
                a, z = r.get('ent', (0, 15))
                seg = out[b * 16 + a:b * 16 + z + 1]
                seg[:] = apply(seg, [r])
    anchors = plan.get('anchor')
    if anchors:
        olab = oklab(col.astype(float)); nlab = oklab(out.astype(float))
        aidx = [b * 16 + i for b in anchors for i in range(1, 16)]
        tol = plan.get('anchor_tol', 0.03)
        for j in range(256):
            if j % 16 == 0 or (j >> 4) in anchors or (j >> 4) in plan.get('no_anchor', ()): continue
            d = np.sqrt(((olab[aidx] - olab[j]) ** 2).sum(1)); k = d.argmin()
            if d[k] < tol:
                w = 1 - d[k] / tol
                tgt = from_oklab(nlab[aidx[k]] + (olab[j] - olab[aidx[k]]))
                out[j] = np.clip(np.round(out[j] * (1 - w) + tgt * w), 0, 255)
    for i, c in plan.get('entries', {}).items(): out[i] = c
    return to555(out.astype(float))
def after(L, plan):
    live, I, m = aligned(L)
    newc = rgb(new_palette(meta[L]['pal'], plan))
    out = recolor_img(live, plan.get('loose', plan.get('default', [])))   # parallax / cycled colours: colour rule
    k = I >= 0; out[k] = newc[I[k]]
    return live, out

def after(L, plan):
    live, I, m = aligned(L)
    old = rgb(meta[L]['pal']); newc = rgb(new_palette(meta[L]['pal'], plan))
    cnt = np.bincount(load(L).ravel(), minlength=256).astype(float) + 0.5
    # colour -> new colour vote (usage-weighted), for pixels the aligned index doesn't cover
    vote = {}
    for i in range(256):
        if i % 16 == 0: continue
        k = tuple(old[i]); vote.setdefault(k, {}); t = tuple(newc[i]); vote[k][t] = vote[k].get(t, 0) + cnt[i]
    lut = {k: max(v, key=v.get) for k, v in vote.items()}
    flat = live.reshape(-1, 3); u, inv = np.unique(flat, axis=0, return_inverse=True)
    loose = apply(u, plan.get('loose', plan.get('default', [])))
    mapped = np.array([lut.get(tuple(c), tuple(loose[j])) for j, c in enumerate(u)], np.uint8)
    out = mapped[inv.ravel()].reshape(live.shape)
    k = I >= 0; out[k] = newc[I[k]]
    return live, out

import struct as _st
_rom = open('/tmp/claude-0/-home-user/972dab79-8ec0-567e-9dbe-b1d16b78ca89/scratchpad/rom.gba', 'rb').read()
def sky_bank(L):
    import sys; sys.path.insert(0, '/home/user/lotrmod/tools/siege')
    from romlib import LEVELS
    e = _st.unpack('<19I', _rom[LEVELS - 0x08000000 + 0x4C * L:][:0x4C])
    if not e[17]: return None
    o = e[17] - 0x08000000 + 36
    w = _st.unpack('<64H', _rom[o:o + 128])
    from collections import Counter
    return Counter(x >> 12 for x in w).most_common(1)[0][0]
def render2(L, plan, crop=True):
    """before/after from the game's own tiles; sky/backdrop pixels taken from the live picture and remapped by the sky bank."""
    idx = load(L); pal = meta[L]['pal']
    old = rgb(pal); newc = rgb(new_palette(pal, plan, meta[L]['palp']))
    bef = old[idx].copy(); aft = newc[idx].copy()
    trans = (idx % 16) == 0
    sb = sky_bank(L)
    try: live, I, m = aligned(L)
    except FileNotFoundError: live = np.zeros((8, 8, 3), np.uint8)
    # place live into render frame
    H, W = live.shape[:2]
    best = None
    ren = old[idx].astype(np.int16)
    for dy in range(0, idx.shape[0] - H + 1):
        for dx in range(0, idx.shape[1] - W + 1):
            mm = (np.abs(ren[dy:dy + H, dx:dx + W] - live).sum(2) < 24).mean()
            if best is None or mm > best[0]: best = (mm, dy, dx)
    _, dy, dx = best
    LV = np.zeros_like(bef); LV[dy:dy + H, dx:dx + W] = live; have = np.zeros(idx.shape, bool); have[dy:dy + H, dx:dx + W] = True
    fill = trans & have
    if fill.any():
        src = LV[fill].astype(float)
        if sb is not None:
            o = old[sb * 16 + 1:sb * 16 + 16].astype(float); n = newc[sb * 16 + 1:sb * 16 + 16].astype(float)
            olab = oklab(o); nlab = oklab(n); slab = oklab(src)
            j = ((slab[:, None, :] - olab[None]) ** 2).sum(2).argmin(1)
            dl = slab - olab[j]; dl[:, 1:] *= 0.25
            res = from_oklab(nlab[j] + dl)
        else:
            res = apply(src.astype(np.uint8), plan.get('loose', plan.get('default', [])))
        bef[fill] = LV[fill]; aft[fill] = np.clip(np.round(res), 0, 255)
    bef[trans & ~have] = 0; aft[trans & ~have] = 0
    return bef, aft, sb
