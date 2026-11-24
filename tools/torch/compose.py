import json, numpy as np
from PIL import Image
spr = json.load(open('sprite.json'))
IRON = {'o': (30, 28, 27), 'd': (56, 52, 49), 'm': (86, 80, 74), 'h': (128, 120, 108), 'r': (172, 162, 142)}
WOOD = [(82, 74, 41), (123, 106, 57), (90, 82, 49)]
def variant(s):
    """lean left (s=-1) or right (s=+1); anchor (0,0) = wall plate, flame upright on a leaning handle"""
    px = {}
    def P(x, y, c, part): px[(s * -x if s > 0 else x, y)] = (*c, part)   # build lean-left, mirror for right
    # handle: bottom (-3, 6) to top (-7, -4), 3 px wide
    hc = {}
    for y in range(6, -5, -1):
        cx = round(-3 + (6 - y) * -0.4)
        hc[y] = cx
        for i, dx in enumerate((-1, 0, 1)): P(cx + dx, y, WOOD[i], 1)
    # ring around the handle (game pole-cap shape in iron)
    rc = hc[2]
    for i, dx in enumerate(range(-2, 3)): P(rc + dx, 2, IRON['dmhmd'[i]], 2)
    for i, dx in enumerate(range(-2, 3)): P(rc + dx, 3, IRON['oddo'[min(i, 3)] if i < 4 else 'o'], 2)
    # arm from plate to ring
    for x in range(rc + 3, -1): P(x, 1, IRON['m'], 2); P(x, 2, IRON['o'], 2)
    # wall plate 2x7 with rivets
    for y in range(-3, 6):
        edge = y in (-3, 5)
        P(-1, y, IRON['o'], 2); P(0, y, IRON['o'] if edge else IRON['m'], 2); P(1, y, IRON['o'] if edge else IRON['d'], 2); P(2, y, IRON['o'], 2)
    P(0, -1, IRON['r'], 2); P(0, 3, IRON['r'], 2); P(1, -1, IRON['o'], 2); P(1, 3, IRON['o'], 2)
    # flame upright on the handle top
    tx, ty = hc[-4], -5
    for dx, dy, r, g, b, _ in [q for q in spr if q[5] == 0]:
        k = 16 - dy
        P(tx + dx + round(-0.12 * k), ty - k, (r, g, b), 0)
    fx, fy = (s * -tx if s > 0 else tx), ty - 7
    # soot on the stone above: tapering, darker low
    rng = np.random.default_rng(11)
    soot = []
    for y in range(0, 13):
        w = 2.6 - y * 0.13
        for x in range(-3, 4):
            if abs(x) > w + rng.uniform(-0.5, 0.5): continue
            soot.append([fx + x, ty - 12 - y, round((0.42 + 0.035 * y + rng.uniform(-0.03, 0.03)) * 100)])
    return {'px': [[x, y, r, g, b, p] for (x, y), (r, g, b, p) in px.items()], 'soot': soot, 'flame': [fx, fy], 'ember': [(s * -tx if s > 0 else tx), ty + 1]}
def front():
    """upright torch on a flat face seen head-on: wall plate below, iron basket holding the handle; anchor (0,0) = plate centre"""
    px = {}
    def P(x, y, c, part): px[(x, y)] = (*c, part)
    # wall plate 5 wide, rows 0..8, dark rim, lit left half, two rivets
    for y in range(0, 9):
        for x in range(-2, 3):
            rim = x in (-2, 2) or y in (0, 8)
            P(x, y, IRON['o'] if rim else (IRON['m'] if x < 0 else IRON['d']), 2)
    for y in (2, 6): P(-1, y, IRON['r'], 2); P(0, y, IRON['h'], 2); P(1, y, IRON['o'], 2)
    # handle: upright, 3 wide, rows -1..-14 (bottom tip in the cup)
    for y in range(-1, -15, -1):
        for i, dx in enumerate((-1, 0, 1)): P(dx, y, WOOD[i], 1)
    # cup: tapered iron point from the plate top up into a ring at -3/-2
    P(0, -1, IRON['o'], 2)
    for dx in (-1, 0, 1): P(dx, -1 if dx else -1, IRON['d'] if dx else IRON['m'], 2)
    for i, dx in enumerate(range(-2, 3)): P(dx, -2, IRON['oddo'[min(i, 3)] if i < 4 else 'o'], 2)
    for i, dx in enumerate(range(-2, 3)): P(dx, -3, IRON['dmhmd'[i]], 2)
    # basket straps up the sides to an upper ring at -8/-9
    for y in range(-7, -3): P(-2, y, IRON['m'], 2); P(2, y, IRON['o'], 2)
    for i, dx in enumerate(range(-2, 3)): P(dx, -8, IRON['oddo'[min(i, 3)] if i < 4 else 'o'], 2)
    for i, dx in enumerate(range(-2, 3)): P(dx, -9, IRON['dmhmd'[i]], 2)
    # flame upright on the handle top
    ty = -15
    for dx, dy, r, g, b, _ in [q for q in spr if q[5] == 0]:
        k = 16 - dy
        P(dx, ty - k, (r, g, b), 0)
    rng = np.random.default_rng(23)
    soot = []
    for y in range(0, 20):
        w = 1.6 + y * 0.12 if y < 8 else 2.6 - (y - 8) * 0.16
        for x in range(-4, 5):
            if abs(x) > w + rng.uniform(-0.5, 0.5): continue
            k = 0.56 + 0.02 * y + 0.04 * abs(x) + rng.uniform(-0.03, 0.03)
            soot.append([x, ty - 3 - y, round(min(0.95, k) * 100)])
    # a soft cast shadow on the stone, down and right of the iron and wood (light from the upper left, as in the game)
    for (x, y), (_, _, _, p) in list(px.items()):
        if p and (x + 1, y + 1) not in px: soot.append([x + 1, y + 1, 72])
    return {'px': [[x, y, r, g, b, p] for (x, y), (r, g, b, p) in px.items()], 'soot': soot, 'flame': [0, ty - 7], 'ember': [0, ty + 1]}
V = {'L': variant(-1), 'R': variant(1), 'F': front()}
json.dump(V, open('mounted.json', 'w'), separators=(',', ':'))
def draw(img, ax, ay, v, lit, ember):
    img = img.astype(float).copy()
    for x, y, k in v['soot']: img[ay + y, ax + x] *= k / 100
    for x, y, r, g, b, part in v['px']:
        if part == 0:
            if not lit:
                if y >= v['ember'][1] - 4: img[ay + y, ax + x] = (24, 20, 18)
                continue
        img[ay + y, ax + x] = (r, g, b)
    if ember:
        ex, ey = v['ember']
        for dx, dy, c in [(0, -3, (150, 26, 10)), (0, -2, (255, 90, 30)), (-1, -1, (210, 40, 14)), (1, -1, (230, 50, 16)), (0, -1, (255, 130, 50))]:
            img[ay + ey + dy, ax + ex + dx] = c
    return np.clip(img, 0, 255).astype(np.uint8)
if __name__ == '__main__':
    day = np.asarray(Image.open('../cy/r112.png').convert('RGB'))
    PL = [(340, 372, 'L'), (516, 372, 'R'), (769, 372, 'L')]
    outs = []
    for lit in (False, True):
        img = day.copy()
        for i, (x, y, side) in enumerate(PL): img = draw(img, x, y, V[side], lit and i < 2, lit and i == 2)
        outs.append(img)
    S = Image.new('RGB', (3 * 335, 2 * 335), (20, 18, 16))
    for r, img in enumerate(outs):
        for i, (x, y, side) in enumerate(PL):
            S.paste(Image.fromarray(img[y - 45:y + 21, x - 33:x + 33]).resize((330, 330), Image.NEAREST), (i * 335, r * 335))
    S.save('mounted-preview.png')
