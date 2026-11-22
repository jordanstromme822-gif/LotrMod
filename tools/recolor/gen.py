from sky import *
import json, plans
GROUPS = [(range(30, 36), plans.DUNHARROW_O), (range(74, 81), plans.MORGUL_O), ([50, 51, 52, 53, 54, 55, 56, 57], plans.ISENGARD_O),
          (range(40, 44), plans.GORGOROTH_O), (range(115, 118), plans.SHELOB_O), ([48], plans.ICE_O), (range(85, 90), plans.DEAD_O),
          ([68], plans.BALCONY_O), (range(122, 130), plans.SNOW_O)]
planOf = {}; pals = {}
for ls, plan in GROUPS:
    for L in ls:
        if L not in meta: continue
        planOf[L] = plan; p = meta[L]['palp']
        new = new_palette(meta[L]['pal'], plan, p)
        b = np.asarray(new, '<u2').tobytes()
        if p in pals: assert pals[p][1] == b, (L, hex(p))
        pals[p] = (L, b)
for p, (L, b) in sorted(pals.items()): print(hex(p), L, len(b), sum(x != y for x, y in zip(b, np.asarray(meta[L]['pal'], '<u2').tobytes())))
FREE_L = [21, 22, 34, 62, 63, 68, 93, 95, 96, 97, 108, 110, 111, 112, 113, 114, 123, 124, 125, 126]
SHADOW_L = [6, 7, 8, 9, 10, 12, 13, 29, 40, 42, 43, 51, 55]
MORGUL_L = [74, 75, 76, 77, 78, 80]
sky = {}
for kind, ls in ((FREE, FREE_L), (SHADOW, SHADOW_L), (MORGULSKY, MORGUL_L)):
    for L in ls:
        plan = planOf.get(L, {}); sb = sky_bank(L)
        base = np.asarray(new_palette(meta[L]['pal'], plan, meta[L]['palp']), '<u2')
        ks = []
        for ph in ('morning', 'noon', 'dusk', 'night'):
            P, _ = phase_plan(L, plan, kind, ph)
            ks.append(np.asarray(new_palette(meta[L]['pal'], P, meta[L]['palp']), '<u2')[sb * 16 + 1: sb * 16 + 16].tobytes().hex())
        sky[L] = [sb, base[sb * 16 + 1: sb * 16 + 16].tobytes().hex(), ks]
json.dump({'pals': [[hex(p), b.hex()] for p, (L, b) in sorted(pals.items())], 'sky': sky}, open('../cycle.json', 'w'))
print(len(sky))
