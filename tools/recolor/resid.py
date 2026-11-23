from compose import *
import plans
AR = {'DUNHARROW': [30,31,32,33,34,35], 'MORGUL': [74,75,76,77,78,79,80], 'ISENGARD': [50,51,52,53,54,55,56,57], 'GORGOROTH': [40,41,42,43],
      'SHELOB': [115,116,117], 'ICE': [48], 'DEAD': [85,86,87,88,89], 'BALCONY': [68], 'SNOW': [122,123,124,125,126,127,128,129]}
def pur(img):
    Lv, C, h = lch(img.reshape(-1, 3).astype(float)); return ((C > 0.035) & (h > 280) & (h < 352) & (Lv > 0.15)).mean() * 100
for k, Ls in AR.items():
    for L in Ls:
        try:
            bef, a, _ = render2(L, getattr(plans, k + '_O')); b = a
        except Exception as e: print(L, 'ERR', e); continue
        print('%-10s %3d %-18s now %5.1f%%  A %5.1f%%  B %5.1f%%' % (k, L, NAMES[L], pur(bef), pur(a), pur(b)), flush=True)
