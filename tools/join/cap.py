"""Close water cut by a joined map edge with a real shoreline copied from the game's own maps.
For each run of open water on the edge, find a place in the source maps where the same tiles sit on one tile line and
the water beyond it closes; copy that water and its shore (A tiles + walking) past the edge."""
import numpy as np, collections
from build import pix

def tmask(k, pixels):
    p = pix(pixels[k[0]])
    if k[1] & 0x400: p = p[:, ::-1]
    if k[1] & 0x800: p = p[::-1]
    return p == 0

def runs(flags):
    out, i = [], 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j < len(flags) and flags[j]: j += 1
            out.append((i, j)); i = j
        else: i += 1
    return out

def rot(G, d):
    """View a grid so that 'outward' is +y (down). d in 's','n','e','w'. Returns accessor functions."""
    return G

def close_edge(GA, GB, GC, edge_tiles, outward, sources, pixels, plain, maxdepth=14, log=None):
    """edge_tiles: list of (y8, x8) along the map edge (inside the map), in order along the edge.
    outward: (dy, dx) unit step from the edge to the outside. sources: list of (A, C) 8 px grids."""
    dy, dx = outward
    # along direction (perpendicular to outward)
    ay, ax = (0, 1) if dy else (1, 0)
    def facing_open(k):
        m = tmask(k, pixels)
        line = m[7] if dy == 1 else m[0] if dy == -1 else m[:, 7] if dx == 1 else m[:, 0]
        return line.any()
    flags = [facing_open(GA[y][x]) for y, x in edge_tiles]
    done = []
    for a, b in runs(flags):
        a0, b0 = max(0, a - 2), min(len(edge_tiles), b + 2)
        pat = [GA[y][x] for y, x in edge_tiles[a0:b0]]
        best = None
        for si, (SA, SC) in enumerate(sources):
            Hs, Ws = len(SA), len(SA[0])
            # source line positions: tile (sy, sx) start of pattern, line along (ay, ax), outward (dy, dx)
            for sy in range(Hs):
                for sx in range(Ws):
                    ey, ex = sy + ay * (len(pat) - 1), sx + ax * (len(pat) - 1)
                    if not (0 <= ey < Hs and 0 <= ex < Ws): continue
                    m = 0
                    for i, k in enumerate(pat):
                        if SA[sy + ay * i][sx + ax * i] == k: m += 1
                    if m < max(3, int(len(pat) * 0.6)): continue
                    # the water beyond must close within maxdepth lines, staying inside the run span (+2)
                    closed_at = None
                    for t in range(1, maxdepth + 1):
                        any_w = False; ok = True
                        for i in range(-2, len(pat) + 2):
                            y, x = sy + ay * i + dy * t, sx + ax * i + dx * t
                            if not (0 <= y < Hs and 0 <= x < Ws): ok = False; break
                            if tmask(SA[y][x], pixels).any():
                                if i < 0 or i >= len(pat): ok = False; break
                                any_w = True
                        if not ok: break
                        if not any_w: closed_at = t; break
                    if closed_at is None: continue
                    score = m * 10 - closed_at
                    if best is None or score > best[0]: best = (score, si, sy, sx, closed_at, m)
        if best is None:
            if log is not None: log.append(('no source', edge_tiles[a], b - a))
            continue
        _, si, sy, sx, depth, m = best; SA, SC = sources[si]
        # copy only the water and its shore: tiles with water, and the tiles touching them that are not plain ground
        wet = set()
        for t in range(1, depth + 1):
            for i in range(-2, len(pat) + 2):
                y, x = sy + ay * i + dy * t, sx + ax * i + dx * t
                if 0 <= y < len(SA) and 0 <= x < len(SA[0]) and tmask(SA[y][x], pixels).any(): wet.add((t, i))
        take = set(wet)
        for (t, i) in wet:
            for dt in (-1, 0, 1):
                for di in (-1, 0, 1):
                    tt, ii = t + dt, i + di
                    if tt < 1: continue
                    y, x = sy + ay * ii + dy * tt, sx + ax * ii + dx * tt
                    if 0 <= y < len(SA) and 0 <= x < len(SA[0]) and plain(SA[y][x]) == 'shore': take.add((tt, ii))
        for (t, i) in take:
            y, x = sy + ay * i + dy * t, sx + ax * i + dx * t
            ty, tx = edge_tiles[a0][0] + ay * i + dy * t, edge_tiles[a0][1] + ax * i + dx * t
            if 0 <= y < len(SA) and 0 <= x < len(SA[0]) and 0 <= ty < len(GA) and 0 <= tx < len(GA[0]):
                GA[ty][tx] = SA[y][x]; GB[ty][tx] = (0, 0); GC[ty][tx] = SC[y][x]
        # the pattern's own edge line: where the source differs from the map edge, the map keeps its tiles
        done.append((edge_tiles[a], b - a, si, depth, m, len(pat)))
        if log is not None: log.append(('closed', edge_tiles[a], b - a, 'src', si, (sy, sx), 'depth', depth, 'match', m, '/', len(pat)))
    return done
