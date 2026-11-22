from lib import *
def hd(a, b): return (a - b + 180) % 360 - 180
def apply(cols, rules):
    """cols: (N,3) uint8 -> (N,3) new. rules: list of dicts with
       h (centre), w (half width, full weight), f (feather), cmin, to (target hue), cs (chroma scale), cset (abs chroma, optional), ls, lo"""
    lab = oklab(cols.astype(float)); Lv = lab[:, 0]; C = np.hypot(lab[:, 1], lab[:, 2]); h = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360
    L2, C2, h2 = Lv.copy(), C.copy(), h.copy()
    for r in rules:
        d = np.abs(hd(h, r['h'])) if 'h' in r else np.zeros_like(h)
        w = np.clip(1 - (d - r.get('w', 30)) / r.get('f', 15), 0, 1)
        cm = r.get('cmin', 0.015); w = w * np.clip((C - cm) / 0.015, 0, 1) if cm > 0 else w
        if 'cmax' in r: w = w * np.clip((r['cmax'] - C) / 0.01, 0, 1)
        if 'lmax' in r: w = w * np.clip((r['lmax'] - Lv) / 0.05, 0, 1)
        if 'lmin' in r: w = w * np.clip((Lv - r['lmin']) / 0.05, 0, 1)
        nh = r['to'] if 'to' in r else h
        if 'mat' in r:
            from mats import ramp
            Lq = Lv * r.get('ls', 1.0) + r.get('lo', 0.0)
            mh, mc = ramp(r['mat'], Lq)
            # keep the original entry-to-entry variety (hue spread round the group's main hue, chroma ratio)
            sel = w > 0
            if sel.sum() > 1:
                ref = np.degrees(np.arctan2((np.sin(np.radians(h)) * C)[sel].sum(), (np.cos(np.radians(h)) * C)[sel].sum()))
                cm = C[sel].mean() + 1e-4
            else: ref, cm = h, C + 1e-4
            nh = mh + r.get('spread', 0.35) * hd(h, ref) * (C > 0.012)
            nc_mat = mc * np.clip((C / cm) ** r.get('cvar', 0.5), 0.6, 1.5) * r.get('cs', 1.0)
        if r.get('keep_spread'): nh = r['to'] + hd(h, r['h']) * r['keep_spread']
        nc = r['cset'] if 'cset' in r else C * r.get('cs', 1.0)
        if 'mat' in r: nc = nc_mat
        nl = Lv * r.get('ls', 1.0) + r.get('lo', 0.0)
        a0, b0 = C2 * np.cos(np.radians(h2)), C2 * np.sin(np.radians(h2))
        a1, b1 = nc * np.cos(np.radians(nh)), nc * np.sin(np.radians(nh))
        aa, bb = a0 + w * (a1 - a0), b0 + w * (b1 - b0)
        C2 = np.hypot(aa, bb); h2 = np.degrees(np.arctan2(bb, aa)) % 360; L2 = L2 + w * (nl - L2)
    a = np.stack([L2, C2 * np.cos(np.radians(h2)), C2 * np.sin(np.radians(h2))], 1)
    return np.clip(np.round(from_oklab(a)), 0, 255).astype(np.uint8)
def recolor_img(img, rules):
    flat = img.reshape(-1, 3); u, inv = np.unique(flat, axis=0, return_inverse=True)
    return apply(u, rules)[inv.ravel()].reshape(img.shape)
