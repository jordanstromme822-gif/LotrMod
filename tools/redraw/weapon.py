"""Original procedural sword for the HD weapons test pack. Not from the game.

Writes skin/standin/weapons/ next to the crisp stand-in. One 128x128 blade in a
130px cell (1 px pad). Straight alpha, un-flipped. Mapped to the stand-in swing
tile keys so the W toggle has something to draw without private art.

usage: python3 -m tools.redraw.weapon [outdir]
"""
import json, os, sys
from .png import write_rgba

BODY, PAD, CELL = 128, 1, 130

def sword():
    alb = bytearray(BODY * BODY * 4)
    nrm = bytearray(BODY * BODY * 4)
    mat = bytearray(BODY * BODY * 4)
    def sdf(x, y):
        # Blade, rounded tip, crossguard, grip, pommel. Coordinates in pixels, y down.
        cx = x - 63.5
        tip = 18.0
        blade_end = 78.0
        if y < blade_end:
            t = max(0.0, min(1.0, (y - tip) / (blade_end - tip)))
            half = 2.0 + t * 7.5
            d = abs(cx) - half
            if y < tip:
                d = ((cx * cx + (y - tip) * (y - tip)) ** 0.5) - 2.2
            return d, 1  # metal
        if y < 86.0:
            d = max(abs(cx) - 22.0, abs(y - 81.5) - 3.2)
            # round the guard ends a little
            ex = abs(cx) - 18.0
            if ex > 0.0:
                d = (ex * ex + (y - 81.5) * (y - 81.5)) ** 0.5 - 3.2
            return d, 1
        if y < 114.0:
            return abs(cx) - 3.4, 0  # grip
        return ((cx * cx + (y - 118.0) * (y - 118.0)) ** 0.5) - 6.5, 1
    def cov(d):
        if d >= 0.6: return 0.0
        if d <= -0.6: return 1.0
        return max(0.0, min(1.0, 0.5 - d))
    for y in range(BODY):
        for x in range(BODY):
            d, metal = sdf(x + 0.5, y + 0.5)
            a = cov(d)
            if a <= 0.0:
                continue
            # Neighbour SDF for a smooth normal (analytic step, not a photo).
            dx = sdf(x + 1.5, y + 0.5)[0] - sdf(x - 0.5, y + 0.5)[0]
            dy = sdf(x + 0.5, y + 1.5)[0] - sdf(x + 0.5, y - 0.5)[0]
            # Author +Y up: image y grows down, so flip the image gradient's y.
            nx, ny, nz = -dx, dy, 0.55
            L = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            nx, ny, nz = nx / L, ny / L, nz / L
            steel = (196, 202, 210) if metal else (92, 62, 36)
            if metal and abs(x + 0.5 - 63.5) < 1.3 and 24 < y < 74:
                steel = (150, 156, 164)  # fuller
            edge = 1.0 if abs(d) < 1.1 and metal else 0.15
            rough = 0.22 if metal else 0.62
            emit = 0.0
            if metal and abs((x + 0.5) - 63.5) < 1.6 and 30 < y < 36:
                emit = 0.85  # a cut glint, not a copied blade
            i = (y * BODY + x) * 4
            alb[i:i + 4] = bytes((steel[0], steel[1], steel[2], int(a * 255 + 0.5)))
            def b8(v):
                return 0 if v < 0 else 255 if v > 255 else int(v + 0.5)
            nrm[i] = b8((nx * 0.5 + 0.5) * 255)
            nrm[i + 1] = b8((ny * 0.5 + 0.5) * 255)
            nrm[i + 2] = b8((nz * 0.5 + 0.5) * 255)
            nrm[i + 3] = b8(a * 255)
            mat[i] = 255 if metal else 40
            mat[i + 1] = int(rough * 255 + 0.5)
            mat[i + 2] = int(edge * 255 + 0.5)
            mat[i + 3] = int(emit * 255 + 0.5)
    def padded(src):
        out = bytearray(CELL * CELL * 4)
        for y in range(BODY):
            dst = ((y + PAD) * CELL + PAD) * 4
            out[dst:dst + BODY * 4] = src[y * BODY * 4:(y + 1) * BODY * 4]
        return out
    return padded(alb), padded(nrm), padded(mat)

def build(outdir):
    alb, nrm, mat = sword()
    os.makedirs(outdir, exist_ok=True)
    write_rgba(os.path.join(outdir, "atlas.png"), CELL, CELL, alb)
    write_rgba(os.path.join(outdir, "normals.png"), CELL, CELL, nrm)
    write_rgba(os.path.join(outdir, "material.png"), CELL, CELL, mat)
    # Swing tiles of the stand-in. A real map lists only weapon FNV keys.
    keys = []
    for i in range(8):
        for ty in (0, 1):
            keys.append("standin:wayfarer/swing/%d/%d" % (i, ty))
    tiles = {k: [0, 0] for k in keys}
    doc = {
        "scale": 16, "cell": CELL, "pad": PAD, "per_row": 1,
        "tiles": tiles,
        "standin": True,
        "note": "Procedural test sword. Copy this folder to the Play Room skin/weapons/ to try it. Real keys are the crisp-skin FNV string.",
    }
    with open(os.path.join(outdir, "map.json"), "w") as f:
        json.dump(doc, f, indent=1)
    return {"cell": CELL, "keys": len(keys)}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "skin", "standin", "weapons")
    print(build(os.path.abspath(out)))
