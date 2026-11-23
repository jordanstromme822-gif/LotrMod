"""The Ring of Isengard as a region block (2026-11-23): a stepped circle of the game's own wall, with the broken Gate.

python3 tools/region/ring.py ROM OUT.pkl [R_UNITS] [UNIT] [GATE]

Every piece is cut from the Flooded Field wall (level 51, rows 106-124 at 8 px):
- runs: wall columns chained so each neighbour pair is one the game's own maps use (no stamped repeats; a source
  column is not reused within 40 columns);
- T1: the wall turning away from the viewer (FF cols 136-143: cap over the corner, the face ending against the wall
  top that runs south); mirrored for the other side;
- T2: a free wall end (FF cols 108-113) with the wall top running north from its cap; mirrored for the other side;
- strip: the wall top seen from above (FF cols 140-143, 6-row period);
- Gate: the broken gap of the FF wall (cols 70-113: crumbled end, a fallen pier, the paved way, the far end).
The circle is pixelated at UNIT tiles (default 18 = 144 px, more than the wall's 17-row height so steps never
overlap); R_UNITS units radius (default 8, 1152 px). Ground spots are left open (None) so the region tool grows its
own ground there; 'CLR' marks the tiles the wall needs cleared of what an earlier block put there.
"""
import collections, pickle, random, sys
sys.path.insert(0, __file__.rsplit('/', 2)[0] + '/join')
from cells import load
from build import pix

rom, out = sys.argv[1:3]
RU = int(sys.argv[3]) if len(sys.argv) > 3 else 8
U = int(sys.argv[4]) if len(sys.argv) > 4 else 18
GATE = sys.argv[5] != '0' if len(sys.argv) > 5 else True
R_, lv, rgb, grids, pixels = load(rom, [50, 51, 55])

def grid8(L):
    g = grids[L]; h, w = len(g), len(g[0])
    A = [[None] * (w * 4) for _ in range(h * 4)]; B = [[None] * (w * 4) for _ in range(h * 4)]; C = [[0] * (w * 4) for _ in range(h * 4)]
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            for k in range(16): A[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]; B[y * 4 + k // 4][x * 4 + k % 4] = c[1][k]; C[y * 4 + k // 4][x * 4 + k % 4] = c[2][k]
    return A, B, C
G8 = {L: grid8(L) for L in (50, 51, 55)}
A, B, C = G8[51]
BL = (0, 0)
HA, HB = set(), set()
for L, (a, b, c) in G8.items():
    for y in range(len(a)):
        for x in range(len(a[0]) - 1): HA.add((a[y][x], a[y][x + 1])); HB.add((b[y][x], b[y][x + 1]))
# plain ground: tiles of the open field below the wall (and the other two maps' open ground)
gc = collections.Counter()
for y in range(128, 151):
    for x in range(0, 131):
        if B[y][x][0] == 0 and C[y][x] == 0: gc[A[y][x]] += 1
for L in (50, 55):
    a, b, c = G8[L]
    for y in range(len(a)):
        for x in range(len(a[0])):
            if b[y][x][0] == 0 and c[y][x] == 0: gc[a[y][x]] += 1
GROUND = {k for k, n in gc.items() if n >= 2}

Y0, NR = 106, 19                     # rows 106..124: 2 walk-behind rows, cap 6, face 10, base 1
def flip(t): return (t[0], t[1] ^ 0x400)
def column(x, keepB_low=False, mirror=False):
    col = []
    for r in range(NR):
        y = Y0 + r; a, b, c = A[y][x], B[y][x], C[y][x]
        if r < 2: col.append(('G', 8)); continue
        if y >= 124 and b[0] and not keepB_low: col.append(('G', 0)); continue        # a stump or branch on the base
        if y >= 115 and not keepB_low: b = BL
        if b[0] == 0 and y >= 124 and (c & 7) == 0: col.append(('G', 0)); continue      # base row: only the blocked shadow stays
        if b[0] == 0 and (a in GROUND or (pix(pixels[a[0]]) == 0).any()): col.append(('G', 0 if y >= 124 else c)); continue
        if mirror: a, b = flip(a), (flip(b) if b[0] else b)
        col.append((a, b, c))
    return col
def piece(x0, x1, mirror=False, keepB=()):
    cols = [column(x, x in keepB, mirror) for x in range(x0, x1 + 1)]
    return cols[::-1] if mirror else cols
BODY = list(range(21, 51)) + list(range(114, 136))
SPOT = set(range(31, 40)) | set(range(120, 130))     # the two weathered patches: at most one per run, in some runs
def sig(x): return [(A[Y0 + r][x], B[Y0 + r][x] if Y0 + r < 115 else BL) for r in range(2, NR)]
SIG = {x: sig(x) for x in range(0, 144)}
def compat(x1, x2):                      # the next column in the source, or a jump where at most one row's pair is new
    if x2 == x1 + 1: return True
    return abs(x2 - x1) > 3 and score(x1, x2) >= 2 * (NR - 2) - 2
def score(x1, x2):  # rows (A and B layer) whose tile pair the game's maps use
    return sum(((p[0], q[0]) in HA) + ((p[1], q[1]) in HB) for p, q in zip(SIG[x1], SIG[x2]))
NEXT = {x: [y for y in BODY if compat(x, y)] for x in BODY}
print('body columns', len(BODY), 'avg successors', sum(map(len, NEXT.values())) / len(BODY))

rng = random.Random(7)
recent = collections.deque(maxlen=40)
def chain(n, left_x=None, right_x=None, spots=False):
    """n body columns; left_x/right_x: source columns (unmirrored) of the pieces on each side, or None."""
    if n <= 0: return []
    body = [y for y in BODY if spots or y not in SPOT]
    # reachability to a good final column
    goodend = [right_x - 1] if right_x is not None and right_x - 1 in body else [y for y in body if right_x is None or score(y, right_x) >= max(score(z, right_x) for z in body) - 1]
    dist = {y: 0 for y in goodend}; frontier = list(goodend)
    while frontier:
        nf = []
        for y in body:
            if y in dist: continue
            if any(z in dist for z in NEXT[y]): dist[y] = min(dist[z] for z in NEXT[y] if z in dist) + 1; nf.append(y)
        frontier = nf
        if not nf: break
    if left_x is None: starts = body
    elif left_x + 1 in body: starts = [left_x + 1]
    else:
        best = max(score(left_x, y) for y in body); starts = [y for y in body if score(left_x, y) >= best - 1]
    used_spot = [False]
    out = []
    cands = [y for y in starts if dist.get(y, 99) <= n - 1]
    for i in range(n):
        if not cands: cands = [y for y in (NEXT[out[-1]] if out else body) if y in dist] or [y for y in body if y in dist] or body
        if used_spot[0] and any(y not in SPOT for y in cands) and not (out and out[-1] in SPOT): cands = [y for y in cands if y not in SPOT]
        fresh = [y for y in cands if y not in recent]
        pick = rng.choice(fresh or cands)
        # stay on the natural next column most of the time (long natural stretches look most like the game's wall)
        if out and out[-1] + 1 in cands and out[-1] + 1 not in recent and rng.random() < 0.8: pick = out[-1] + 1
        out.append(pick); recent.append(pick)
        if pick in SPOT: used_spot[0] = True
        rem = n - 1 - i
        cands = [y for y in NEXT[pick] if y in body and dist.get(y, 99) <= rem - 1] if rem else []
    return [column(x) for x in out]

T1E = piece(136, 143, keepB=(140, 141, 142, 143))
T1W = piece(136, 143, mirror=True, keepB=(140, 141, 142, 143))
for p_ in (T1E, T1W):
    for col in p_:
        col[0] = col[1] = ('G', 8)
T2W = piece(108, 113)
for k in range(3):
    for r in range(2, 4): T2W[k][r] = ('G', 8)
T2E = [[(e if e[0] == 'G' else (flip(e[0]), flip(e[1]) if e[1][0] else e[1], e[2])) for e in col] for col in T2W[::-1]]
GATEP = piece(70, 113)
for k in range(38, 41):                       # the far wall's free end: no moss bits on its top (as T2W)
    for r in range(2, 4): GATEP[k][r] = ('G', 8)
# a fallen stretch of the gate's wall in the gap, against the far end: the Campsite's broken low wall (level 50,
# cols 26-35, rows 83-91; its shadow row 91 on the wall's base row)
A50, B50, C50 = G8[50]
for k, x in enumerate(range(26, 36)):
    for r, y in enumerate(range(83, 92)):
        a, b, c = A50[y][x], B50[y][x], C50[y][x]
        if b[0] == 0 and (a in GROUND or (pix(pixels[a[0]]) == 0).any()): continue
        GATEP[28 + k][10 + r] = (a, b, c)
def strip_row(fy, mirror):                     # the wall top at FF row fy (period 12 past row 146: B 4, A 6)
    if fy > 146: fy = 132 + (fy - 132) % 12
    row = [(A[fy][x], B[fy][x], C[fy][x]) for x in range(140, 144)]
    return [(flip(t[0]), flip(t[1]) if t[1][0] else t[1], t[2]) for t in row[::-1]] if mirror else row

# ---- the stepped circle -------------------------------------------------------------------------------------------
inside = {(i, j) for i in range(-RU, RU) for j in range(-RU, RU) if (i + 0.5) ** 2 + (j + 0.5) ** 2 <= RU * RU}
hedges = []                                    # (Y, X0, X1) unit coords
for j in range(-RU, RU + 1):
    for kind in ('top', 'bot'):
        xs = sorted(i for i in range(-RU, RU) if ((i, j) in inside and (i, j - 1) not in inside) if kind == 'top') if kind == 'top' else \
             sorted(i for i in range(-RU, RU) if ((i, j - 1) in inside and (i, j) not in inside))
        run = []
        for i in xs + [None]:
            if run and (i is None or i != run[-1] + 1): hedges.append((j, run[0], run[-1] + 1, kind)); run = []
            if i is not None: run.append(i)
vedges = []                                    # (X, Y0, Y1)
for i in range(-RU, RU + 1):
    ys = sorted(j for j in range(-RU, RU) if ((i, j) in inside) != ((i - 1, j) in inside))
    run = []
    for j in ys + [None]:
        if run and (j is None or j != run[-1] + 1): vedges.append((i, run[0], run[-1] + 1)); run = []
        if j is not None: run.append(j)
def vdir(X, Y):
    for (x, y0, y1) in vedges:
        if x == X and y0 == Y: return 'down'
        if x == X and y1 == Y: return 'up'
    raise SystemExit('no vertical edge at %d,%d' % (X, Y))

PAD = 12
S = (RU * U + PAD) // 4 * 4 + 4               # half size in tiles, whole cells
W8, H8 = 2 * S, 2 * S + 24
GA = [[None] * W8 for _ in range(H8)]; GB = [[BL] * W8 for _ in range(H8)]; GC = [[None] * W8 for _ in range(H8)]
wall = [[False] * W8 for _ in range(H8)]
def put(x, y, e):
    if not (0 <= x < W8 and 0 <= y < H8): return
    if e[0] == 'G':
        GA[y][x] = None; GB[y][x] = BL; GC[y][x] = e[1]
    else:
        GA[y][x], GB[y][x], GC[y][x] = e; wall[y][x] = True
def put_cols(x0, ytop, cols):
    for k, col in enumerate(cols):
        for r, e in enumerate(col): put(x0 + k, ytop - 2 + r, e)
gate_at = None
for (Y, X0, X1, kind) in hedges:
    xl, xr, yt = S + X0 * U, S + X1 * U, S + Y * U
    ld, rd = vdir(X0, Y), vdir(X1, Y)
    lp, lx0, lsrc = (T1W, xl - 2, 136) if ld == 'down' else (T2W, xl - 5, 113)
    rp, rsrc = (T1E, 136) if rd == 'down' else (T2E, 113)
    rx0 = xr - 6 if rd == 'down' else xr - 1
    n = rx0 - (lx0 + len(lp))
    put_cols(lx0, yt, lp)
    # next to a mirrored piece, a few mirrored columns that follow it in the source (its natural neighbours)
    if lp is T1W: lead = [column(x, mirror=True) for x in range(135, 129, -1)]; put_cols(lx0 + len(lp), yt, lead); lx0 += len(lead)
    if rp is T2E:
        tail = [column(x, mirror=True) for x in range(119, 113, -1)]; rx0 -= len(tail); put_cols(rx0, yt, tail)
        rp_cols = tail + rp
    n = rx0 - (lx0 + len(lp))
    spots = rng.random() < 0.35
    if GATE and kind == 'bot' and Y == max(h[0] for h in hedges) and n >= len(GATEP) + 8:
        a = (n - len(GATEP)) // 2
        put_cols(lx0 + len(lp), yt, chain(a, 113 if lp is T2W else None, 70))
        put_cols(lx0 + len(lp) + a, yt, GATEP); gate_at = (lx0 + len(lp) + a, yt)
        put_cols(lx0 + len(lp) + a + len(GATEP), yt, chain(n - a - len(GATEP), 113, None))
    else:
        put_cols(lx0 + len(lp), yt, chain(n, 113 if lp is T2W else None, 136 if rp is T1E else None, spots))
    put_cols(rx0 + (6 if rp is T2E else 0), yt, rp)
for (X, Y0_, Y1_) in vedges:
    x = S + X * U - 2; top = S + Y0_ * U; ya, yb = top + 6, S + Y1_ * U
    # which side the upper run lies on decides the mirroring (the strip's lit side faces the same way as T1's)
    up = [h for h in hedges if h[0] == Y0_ and (h[1] == X or h[2] == X)]
    mir = bool(up) and up[0][1] == X          # upper run starts here (extends east): mirrored T1 at its west end
    for y in range(ya, yb):
        row = strip_row(108 + y - top, mir)
        for k in range(4): put(x + k, y, row[k])
    # the strip ends on the lower run's cap: the 2 walk-behind rows there are wall top too
CLR = [[False] * W8 for _ in range(H8)]
for y in range(H8):
    for x in range(W8):
        if wall[y][x]:
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    if 0 <= y + dy < H8 and 0 <= x + dx < W8: CLR[y + dy][x + dx] = True
H8c = (H8 + 3) // 4 * 4
while len(GA) < H8c: GA.append([None] * W8); GB.append([BL] * W8); GC.append([None] * W8); CLR.append([False] * W8)
pickle.dump(dict(GA=GA, GB=GB, GC=GC, W=W8 // 4, H=H8c // 4, CLR=CLR, centre8=(S, S), gate8=gate_at, R8=RU * U), open(out, 'wb'))
print('ring', W8 // 4, 'x', H8c // 4, 'cells; centre tile', (S, S), 'gate at', gate_at, 'h edges', len(hedges), 'v edges', len(vedges))
