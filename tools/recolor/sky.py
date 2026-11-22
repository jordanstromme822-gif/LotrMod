from compose import *
import plans, copy
# sky phase ramps: t (0 = darkest sky colour in the bank, 1 = brightest cloud) -> (L, hue, C)
FREE = {
 'morning': [(0.0, 0.62, 250, 0.045), (0.45, 0.78, 60, 0.050), (0.8, 0.88, 80, 0.055), (1.0, 0.96, 90, 0.030)],
 'noon':    [(0.0, 0.62, 245, 0.090), (0.5, 0.76, 238, 0.065), (0.8, 0.90, 230, 0.025), (1.0, 0.98, 220, 0.008)],
 'dusk':    [(0.0, 0.38, 270, 0.060), (0.4, 0.58, 30, 0.110), (0.75, 0.74, 52, 0.130), (1.0, 0.88, 75, 0.090)],
 'night':   [(0.0, 0.25, 265, 0.055), (0.5, 0.35, 260, 0.050), (0.85, 0.49, 250, 0.035), (1.0, 0.61, 240, 0.025)],   # v246: lighter, the page's night look darkens it again
}
SHADOW = {
 'morning': [(0.0, 0.40, 40, 0.020), (0.5, 0.58, 50, 0.030), (1.0, 0.78, 65, 0.035)],
 'noon':    [(0.0, 0.50, 60, 0.012), (0.5, 0.66, 65, 0.016), (1.0, 0.84, 75, 0.018)],
 'dusk':    [(0.0, 0.28, 30, 0.050), (0.5, 0.45, 35, 0.090), (1.0, 0.66, 50, 0.110)],
 'night':   [(0.0, 0.12, 30, 0.020), (0.5, 0.20, 30, 0.035), (1.0, 0.34, 35, 0.060)],
}
GRADE = {'morning': (1.0, 70, 0.012), 'noon': (1.0, None, 0), 'dusk': (0.9, 50, 0.025), 'night': (0.55, 255, 0.02)}
def ramp(keys, t):
    k = np.array(keys); a = np.cos(np.radians(k[:, 2])) * k[:, 3]; b = np.sin(np.radians(k[:, 2])) * k[:, 3]
    return np.stack([np.interp(t, k[:, 0], k[:, 1]), np.interp(t, k[:, 0], a), np.interp(t, k[:, 0], b)], -1)
def phase_plan(L, plan, kind, ph):
    sb = sky_bank(L); P = copy.deepcopy(plan); base = rgb(new_palette(meta[L]['pal'], plan, meta[L]['palp']))
    ent = {}
    if sb is not None:
        cols = base[sb * 16 + 1:sb * 16 + 16].astype(float); Lv = oklab(cols)[:, 0]
        t = (Lv - Lv.min()) / max(1e-3, Lv.max() - Lv.min())
        new = np.clip(np.round(from_oklab(ramp(kind[ph], t))), 0, 255).astype(np.uint8)
        for i in range(15): ent[sb * 16 + 1 + i] = new[i]
    P['entries'] = ent
    return P, sb
def grade(img, mask, ph):
    k, hue, c = GRADE[ph]
    if hue is None: return img
    lab = oklab(img[mask].astype(float)); lab[:, 0] *= k
    lab[:, 1:] = lab[:, 1:] * (0.6 if ph == 'night' else 0.95) + np.array([np.cos(np.radians(hue)), np.sin(np.radians(hue))]) * c
    out = img.copy(); out[mask] = np.clip(np.round(from_oklab(lab)), 0, 255); return out
def render_phase(L, plan, kind, ph):
    P, sb = phase_plan(L, plan, kind, ph)
    _, aft, _ = render2(L, P)
    idx = load(L); ground = ((idx % 16) != 0) & ((idx >> 4) != (sb if sb is not None else -1))
    return grade(aft, ground, ph)
MORGULSKY = {
 'morning': [(0.0, 0.34, 200, 0.020), (0.5, 0.50, 175, 0.028), (1.0, 0.74, 150, 0.040)],
 'noon':    [(0.0, 0.44, 190, 0.016), (0.5, 0.60, 170, 0.022), (1.0, 0.82, 145, 0.032)],
 'dusk':    [(0.0, 0.26, 210, 0.022), (0.5, 0.40, 160, 0.035), (1.0, 0.66, 120, 0.060)],
 'night':   [(0.0, 0.18, 200, 0.020), (0.5, 0.29, 175, 0.032), (1.0, 0.56, 150, 0.060)],
}
SHADOW_GRADE = {'morning': (0.95, 45, 0.010), 'noon': (1.0, None, 0), 'dusk': (0.85, 35, 0.030), 'night': (0.55, 30, 0.015)}
_grade0 = grade
def grade(img, mask, ph, table=None):
    global GRADE
    if table is None: return _grade0(img, mask, ph)
    old = GRADE; GRADE = table
    try: return _grade0(img, mask, ph)
    finally: GRADE = old
def render_phase(L, plan, kind, ph):
    P, sb = phase_plan(L, plan, kind, ph)
    _, aft, _ = render2(L, P)
    idx = load(L); ground = ((idx % 16) != 0) & ((idx >> 4) != (sb if sb is not None else -1))
    return grade(aft, ground, ph, None if kind is FREE else SHADOW_GRADE)
MORGUL_GRADE = {'morning': (0.95, 170, 0.008), 'noon': (1.0, None, 0), 'dusk': (0.85, 160, 0.015), 'night': (0.55, 175, 0.015)}
def render_phase(L, plan, kind, ph):
    P, sb = phase_plan(L, plan, kind, ph)
    _, aft, _ = render2(L, P)
    idx = load(L); ground = ((idx % 16) != 0) & ((idx >> 4) != (sb if sb is not None else -1))
    tab = None if kind is FREE else (MORGUL_GRADE if kind is MORGULSKY else SHADOW_GRADE)
    return grade(aft, ground, ph, tab)
