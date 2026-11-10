"""Snap colours onto the GBA's 5-bit steps and keep a short palette."""

def rgb555(rgb):
    return tuple(min(248, (c // 8) * 8) for c in rgb)

def limit(colors, cap=15):
    """colours is a list of (r,g,b) already used. Drop extras, nearest-neighbour onto the kept set."""
    uniq = []
    for c in colors:
        c = rgb555(c)
        if c not in uniq:
            uniq.append(c)
    if len(uniq) <= cap:
        return uniq
    kept = uniq[:cap]
    return kept

def nearest(c, palette):
    c = rgb555(c)
    best, bd = palette[0], 1e9
    for p in palette:
        d = (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2
        if d < bd:
            best, bd = p, d
    return best
