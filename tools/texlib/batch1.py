# Texture library batch 1 (Jordan, 2026-11-10): our own rocks, trees, bushes and path tiles, drawn procedurally
# at GBA size (15-bit colour, small ramps, dark outline, light from the top left, like the game's own art).
import numpy as np, random, os
from PIL import Image
OUT = os.environ.get("OUT", "out"); os.makedirs(OUT, exist_ok=True)
def q(c): return tuple(min(248, max(0, int(round(v / 8.0)) * 8)) for v in c)            # GBA 15-bit colour
def ramp(dark, light, n=5): return [q([dark[i] + (light[i] - dark[i]) * k / (n - 1) for i in range(3)]) for k in range(n)]
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
def vnoise(h, w, cell, seed, wrap=False):
    r = np.random.RandomState(seed); gh, gw = h // cell + 2, w // cell + 2
    g = r.rand(gh, gw)
    if wrap: g[:, -2:] = g[:, :2]; g[-2:, :] = g[:2, :]; gh2, gw2 = h // cell, w // cell; g[gh2:, :] = g[:gh - gh2, :]; g[:, gw2:] = g[:, :gw - gw2]
    y, x = np.mgrid[0:h, 0:w] / cell; i, j = y.astype(int), x.astype(int); fy, fx = y - i, x - j
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b, c, d = g[i, j], g[i, j + 1], g[i + 1, j], g[i + 1, j + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
def fbm(h, w, seed, cells=(8, 4, 2), wrap=False):
    s = sum(vnoise(h, w, c, seed + k, wrap) / (k + 1) for k, c in enumerate(cells)); return (s - s.min()) / (s.max() - s.min() + 1e-9)
def shade(level, pal, y0=0, x0=0):
    # level 0..1 -> palette index with ordered dithering between steps
    h, w = level.shape; n = len(pal); t = np.clip(level, 0, 0.999) * (n - 1)
    b = BAYER[(np.arange(h)[:, None] + y0) % 4, (np.arange(w)[None, :] + x0) % 4]
    idx = np.clip(np.floor(t + (b - 0.5) * 0.55 + 0.5).astype(int), 0, n - 1); return idx
def paint(mask, idx, pal, outline=(16, 16, 24)):
    h, w = mask.shape; img = np.zeros((h, w, 4), np.uint8)
    P = np.array(pal, np.uint8); img[..., :3] = P[idx]; img[..., 3] = np.where(mask, 255, 0)
    # 1 px dark outline around the shape
    m = mask.astype(bool); edge = np.zeros_like(m)
    edge[1:, :] |= m[:-1, :]; edge[:-1, :] |= m[1:, :]; edge[:, 1:] |= m[:, :-1]; edge[:, :-1] |= m[:, 1:]   # no wrap-around
    edge &= ~m; img[edge, :3] = q(outline); img[edge, 3] = 255; return img
def light_from_height(hgt, k=2.2):
    gy, gx = np.gradient(hgt); nx, ny, nz = -gx * k, -gy * k, np.ones_like(hgt)
    L = np.array([-0.55, -0.65, 0.52]); L /= np.linalg.norm(L); n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / n, 0, 1)

def boulder(w, h, seed, pal, moss=None, cracks=2):
    r = random.Random(seed); y, x = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = w / 2, h * 0.55; rx, ry = w * 0.44, h * 0.42
    ang = np.arctan2(y - cy, x - cx); wob = 1 + 0.10 * np.sin(ang * 3 + r.random() * 6) + 0.07 * np.sin(ang * 5 + r.random() * 6)
    d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2) / wob
    mask = d < 1.0; mask[int(cy + ry * 0.75):, :] &= d[int(cy + ry * 0.75):, :] < 0.97   # flatter base
    hgt = np.sqrt(np.clip(1 - d * d, 0, 1)) + fbm(h, w, seed, (6, 3)) * 0.35
    lv = light_from_height(hgt * 6) * 0.85 + 0.12 - (y / h) * 0.1
    lv[~mask] = 0; idx = shade(lv, pal)
    # facets: a few darker plane breaks
    for _ in range(cracks):
        px, py = r.uniform(cx - rx * 0.4, cx + rx * 0.4), r.uniform(cy - ry * 0.5, cy + ry * 0.2); a = r.uniform(0.6, 2.4)
        for t in range(int(w * 0.35)):
            xi, yi = int(px), int(py)
            if 0 <= xi < w and 0 <= yi < h and mask[yi, xi] and d[yi, xi] < 0.85: idx[yi, xi] = 0
            a += r.uniform(-0.5, 0.5); px += np.cos(a); py += np.sin(a) * 0.8
    img = paint(mask, idx, pal)
    if moss:
        mn = fbm(h, w, seed + 9, (4, 2)); up = (lv > 0.55) & mask & (mn > 0.5) & (y < cy)
        mi = shade(np.clip((mn - 0.5) * 2.2 + lv * 0.3, 0, 1), moss); P = np.array(moss, np.uint8)
        img[up, :3] = P[mi[up]]
    return img

def leafy_tree(w, h, seed, leaf, bark):
    r = random.Random(seed); img = np.zeros((h, w, 4), np.uint8); y, x = np.mgrid[0:h, 0:w].astype(float)
    # trunk with flared roots
    tx = w / 2; trunk = (np.abs(x - tx) < (2.2 + np.clip((y - h * 0.82) * 0.5, 0, 4))) & (y > h * 0.45) & (y < h * 0.95)
    tl = np.clip(0.75 - (x - tx + 2) * 0.18, 0, 1) * (0.5 + 0.5 * fbm(h, w, seed + 3, (2, 1)))
    timg = paint(trunk, shade(tl, bark), bark)
    # canopy: overlapping lumps, each lit like a ball
    hgt = np.full((h, w), -1.0)
    lumps = [(tx + r.uniform(-w * 0.28, w * 0.28), r.uniform(h * 0.14, h * 0.5), r.uniform(w * 0.17, w * 0.25)) for _ in range(9)]
    lumps.sort(key=lambda l: l[1])
    for (lx, ly, lr) in lumps:
        dd = ((x - lx) ** 2 + (y - ly) ** 2) / lr ** 2; inside = dd < 1
        hgt = np.where(inside, np.maximum(hgt, np.sqrt(np.clip(1 - dd, 0, 1)) + ly / h * 0.2), hgt)
    cm = hgt > -1; hgt[~cm] = 0
    leafn = fbm(h, w, seed + 5, (3, 2, 1))
    lv = light_from_height(hgt * 7, 1.6) * 0.75 + leafn * 0.3 - 0.05; lv[~cm] = 0
    cimg = paint(cm, shade(lv, leaf), leaf, outline=(8, 24, 16))
    out = timg.copy(); a = cimg[..., 3] > 0; out[a] = cimg[a]
    # ground shadow
    sh = ((x - tx - 3) / (w * 0.42)) ** 2 + ((y - h * 0.94) / (h * 0.06)) ** 2 < 1
    shadow = sh & (out[..., 3] == 0); out[shadow] = (0, 0, 0, 90)
    return out

def pine(w, h, seed, leaf, bark):
    r = random.Random(seed); y, x = np.mgrid[0:h, 0:w].astype(float); tx = w / 2
    trunk = (np.abs(x - tx) < 2) & (y > h * 0.78) & (y < h * 0.95)
    out = paint(trunk, shade(np.clip(0.8 - (x - tx + 2) * 0.2, 0, 1), bark), bark)
    cm = np.zeros((h, w), bool); hgt = np.zeros((h, w))
    tiers = 5
    for k in range(tiers):
        top = h * 0.04 + k * h * 0.15; bot = top + h * 0.26; half = w * (0.16 + k * 0.075)
        t = (y - top) / (bot - top); jag = 1 + 0.12 * np.sin(x * 1.7 + k) * (t > 0.7)
        inside = (t >= 0) & (t <= 1) & (np.abs(x - tx) < half * t * jag)
        hgt = np.where(inside, 1 - np.abs(x - tx) / (half + 1) * 0.8 + t * 0.2, hgt); cm |= inside
    lv = np.clip(0.95 - (x - tx + w * 0.12) / w * 1.3, 0, 1) * 0.7 + fbm(h, w, seed, (2, 1)) * 0.3
    for k in range(tiers):   # darker underside of each tier
        bot = h * 0.04 + k * h * 0.15 + h * 0.26; lv[(y > bot - 2.5) & (y < bot + 0.5)] *= 0.45
    lv[~cm] = 0; cimg = paint(cm, shade(lv, leaf), leaf, outline=(8, 20, 16))
    a = cimg[..., 3] > 0; out[a] = cimg[a]
    sh = ((x - tx - 2) / (w * 0.36)) ** 2 + ((y - h * 0.94) / (h * 0.045)) ** 2 < 1
    out[sh & (out[..., 3] == 0)] = (0, 0, 0, 90); return out

def dead_tree(w, h, seed, bark):
    r = random.Random(seed); lv = np.zeros((h, w)); m = np.zeros((h, w), bool)
    def branch(x0, y0, ang, length, th, depth):
        x1, y1 = x0 + np.cos(ang) * length, y0 + np.sin(ang) * length
        steps = int(length * 2) + 1
        for s in range(steps + 1):
            t = s / steps; px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t; tt = th * (1 - t * 0.35)
            for yy in range(int(py - tt - 1), int(py + tt + 2)):
                for xx in range(int(px - tt - 1), int(px + tt + 2)):
                    if 0 <= xx < w and 0 <= yy < h and (xx - px) ** 2 + (yy - py) ** 2 <= tt * tt + 0.3:
                        m[yy, xx] = True; lv[yy, xx] = max(lv[yy, xx], np.clip(0.75 - (xx - px) / (tt + 0.5) * 0.35 - (yy / h) * 0.15, 0.05, 1))
        if depth == 0 or th < 0.6: return
        k = 3 if depth > 2 else 2
        for i in range(k):
            spread = (i - (k - 1) / 2) * 0.7 + r.uniform(-0.25, 0.25)
            branch(x1, y1, ang + spread, length * r.uniform(0.55, 0.72), th * 0.62, depth - 1)
    branch(w / 2, h * 0.95, -np.pi / 2 + r.uniform(-0.12, 0.12), h * 0.34, 3.4, 4)
    for a in (2.6, 0.5):   # roots
        branch(w / 2, h * 0.9, a, w * 0.16, 1.8, 0)
    lv = lv * (0.7 + 0.3 * fbm(h, w, seed + 1, (2, 1)))
    out = paint(m, shade(lv, bark), bark)
    y, x = np.mgrid[0:h, 0:w].astype(float)
    sh = ((x - w / 2 - 3) / (w * 0.3)) ** 2 + ((y - h * 0.95) / (h * 0.04)) ** 2 < 1
    out[sh & (out[..., 3] == 0)] = (0, 0, 0, 80); return out

def bush(w, h, seed, leaf, berries=None):
    r = random.Random(seed); y, x = np.mgrid[0:h, 0:w].astype(float); hgt = np.full((h, w), -1.0)
    for _ in range(6):
        lx, ly, lr = w / 2 + r.uniform(-w * 0.25, w * 0.25), h * r.uniform(0.45, 0.65), r.uniform(w * 0.2, w * 0.3)
        dd = ((x - lx) ** 2 + ((y - ly) * 1.3) ** 2) / lr ** 2; hgt = np.where(dd < 1, np.maximum(hgt, np.sqrt(np.clip(1 - dd, 0, 1))), hgt)
    m = hgt > -1; hgt[~m] = 0
    lv = light_from_height(hgt * 5, 1.5) * 0.7 + fbm(h, w, seed, (2, 1)) * 0.35 - 0.05; lv[~m] = 0
    out = paint(m, shade(lv, leaf), leaf, outline=(8, 24, 16))
    if berries:
        for _ in range(7):
            bx, by = int(w / 2 + r.uniform(-w * 0.3, w * 0.3)), int(h * r.uniform(0.35, 0.7))
            if m[by, bx]: out[by, bx, :3] = q(berries); out[by - 1, bx, :3] = q((255, 220, 220))
    return out

def cobble(sz, seed, pal, mortar):
    # seamless stones: Voronoi on a wrapped grid, each stone bevelled
    r = np.random.RandomState(seed); n = 6; pts = []
    for i in range(n):
        for j in range(n): pts.append(((i + 0.2 + r.rand() * 0.6) * sz / n, (j + 0.2 + r.rand() * 0.6) * sz / n))
    pts = np.array(pts); y, x = np.mgrid[0:sz, 0:sz].astype(float)
    d1 = np.full((sz, sz), 1e9); d2 = np.full((sz, sz), 1e9); cid = np.zeros((sz, sz), int)
    for k, (px, py) in enumerate(pts):
        for ox in (-sz, 0, sz):
            for oy in (-sz, 0, sz):
                d = np.sqrt((x - px - ox) ** 2 + (y - py - oy) ** 2)
                closer = d < d1; d2 = np.where(closer, d1, np.minimum(d2, d)); cid = np.where(closer, k, cid); d1 = np.where(closer, d, d1)
    edge = d2 - d1; tone = r.rand(len(pts))[cid]
    hgt = np.clip(edge / 3.0, 0, 1)
    gy = np.roll(hgt, 1, 0) - hgt; gx = np.roll(hgt, 1, 1) - hgt
    lv = 0.45 + tone * 0.25 + (gy + gx) * 0.55 + (fbm(sz, sz, seed, (4, 2), wrap=True) - 0.5) * 0.25
    lv = np.clip(lv * (hgt > 0.3) + 0.0, 0, 1); idx = shade(lv, pal)
    img = np.zeros((sz, sz, 4), np.uint8); img[..., :3] = np.array(pal, np.uint8)[idx]; img[..., 3] = 255
    mo = edge < 1.1; mi = shade(np.clip(0.3 + fbm(sz, sz, seed + 2, (2, 1), wrap=True) * 0.5, 0, 1), mortar)
    img[mo, :3] = np.array(mortar, np.uint8)[mi[mo]]; return img

def dirt(sz, seed, pal, pebble):
    r = np.random.RandomState(seed); n = fbm(sz, sz, seed, (8, 4, 2), wrap=True)
    img = np.zeros((sz, sz, 4), np.uint8); img[..., :3] = np.array(pal, np.uint8)[shade(0.25 + n * 0.55, pal)]; img[..., 3] = 255
    for _ in range(14):   # pebbles with a lit top and a shadow under
        px, py = r.randint(0, sz), r.randint(0, sz); s = r.choice((1, 1, 2))
        for dy in range(-s, s + 1):
            for dx in range(-s, s + 1):
                if dx * dx + dy * dy <= s * s: img[(py + dy) % sz, (px + dx) % sz, :3] = pebble[2 if dy < 0 else 1]
        img[(py + s + 1) % sz, px % sz, :3] = pebble[0]
    return img

def grass_edge(sz, seed, grass, dirtpal):
    # path tile with grass creeping in at both sides (seamless top to bottom)
    base = dirt(sz, seed, dirtpal, ramp((40, 32, 24), (200, 184, 160), 3)); y, x = np.mgrid[0:sz, 0:sz].astype(float)
    n = fbm(sz, sz, seed + 4, (4, 2), wrap=True); side = np.minimum(x, sz - 1 - x) + n * 6
    g = side < 7; gi = shade(np.clip(0.3 + n * 0.6 - (side < 1.5) * 0.2, 0, 1), grass)
    base[g, :3] = np.array(grass, np.uint8)[gi[g]]
    blades = (side >= 6) & (side < 8) & ((x.astype(int) + y.astype(int) * 3) % 4 == 0); base[blades, :3] = grass[1]
    return base

PAL = {
    "stone": ramp((40, 40, 48), (200, 200, 208)), "warm_stone": ramp((48, 40, 32), (216, 200, 168)), "dark_stone": ramp((24, 24, 32), (128, 120, 128)),
    "moss": ramp((24, 56, 24), (136, 176, 72), 4), "leaf": ramp((16, 48, 24), (144, 200, 88)), "autumn": ramp((64, 24, 16), (248, 184, 72)),
    "pine": ramp((8, 32, 24), (88, 152, 96)), "bark": ramp((32, 24, 16), (152, 112, 72), 4), "deadbark": ramp((32, 28, 28), (176, 160, 144), 4),
    "dirt": ramp((72, 48, 32), (176, 136, 96)), "cob": ramp((48, 48, 56), (192, 184, 176)), "mortar": ramp((24, 24, 24), (72, 64, 56), 3),
    "grass": ramp((24, 64, 24), (128, 184, 72)), "sand": ramp((120, 96, 64), (232, 208, 160)),
}
pieces = {
    "rock-boulder-grey": boulder(28, 22, 3, PAL["stone"]),
    "rock-boulder-mossy": boulder(30, 24, 7, PAL["stone"], moss=PAL["moss"]),
    "rock-boulder-sandstone": boulder(26, 20, 11, PAL["warm_stone"], cracks=3),
    "rock-small-dark": boulder(14, 11, 21, PAL["dark_stone"], cracks=1),
    "rock-pile": None,
    "tree-oak": leafy_tree(40, 52, 4, PAL["leaf"], PAL["bark"]),
    "tree-autumn": leafy_tree(40, 52, 12, PAL["autumn"], PAL["bark"]),
    "tree-pine": pine(30, 56, 5, PAL["pine"], PAL["bark"]),
    "tree-dead": dead_tree(40, 54, 8, PAL["deadbark"]),
    "bush-green": bush(22, 16, 2, PAL["leaf"]),
    "bush-berries": bush(22, 16, 6, PAL["leaf"], berries=(200, 32, 48)),
    "path-cobblestone": cobble(32, 1, PAL["cob"], PAL["mortar"]),
    "path-dirt": dirt(32, 5, PAL["dirt"], ramp((40, 32, 24), (200, 184, 160), 3)),
    "path-dirt-grass-edges": grass_edge(32, 9, PAL["grass"], PAL["dirt"]),
    "path-sand": dirt(32, 13, PAL["sand"], ramp((96, 80, 56), (248, 232, 200), 3)),
}
# rock pile: three small rocks together
pile = np.zeros((20, 30, 4), np.uint8)
for (ox, oy, s, sd) in ((0, 6, 14, 31), (14, 7, 15, 32), (7, 0, 13, 33)):
    b = boulder(s, int(s * 0.8), sd, PAL["stone"], cracks=1); hh, ww = b.shape[:2]
    reg = pile[oy:oy + hh, ox:ox + ww]; a = b[..., 3] > 0; reg[a[:reg.shape[0], :reg.shape[1]]] = b[:reg.shape[0], :reg.shape[1]][a[:reg.shape[0], :reg.shape[1]]]
pieces["rock-pile"] = pile
for k, v in pieces.items(): Image.fromarray(v, "RGBA").save(f"{OUT}/{k}.png")
print(len(pieces), "pieces")
