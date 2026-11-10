"""Original stand-in: a wayfarer drawn at 2x by hand, not taken from the game.

No character sheets are in the repo (tools/colorplan reads local captures only).
This figure is a placeholder so the atlas path has something to pack. It is labelled
standin in every key. usage: python3 -m tools.redraw.standin [outdir]
"""
import json, os, sys
from .cycles import anim_map, walk_and_swing
from .pack import grid_rgba, pack

PAL = {
    "k": (24, 16, 16),
    "s": (240, 176, 128),
    "h": (104, 64, 32),
    "e": (40, 32, 32),
    "c": (56, 96, 56),
    "d": (32, 64, 40),
    "l": (144, 96, 48),
    "m": (184, 184, 192),
    "b": (72, 40, 24),
}

# 16x32: one tile wide, two tall, each pixel a hand-placed 2x texel (not a doubled 8x8).
IDLE = [
    "................",
    "................",
    ".....kkkk.......",
    "....kssssk......",
    "....kssssk......",
    "....khhssk......",
    "....kseesk......",
    "....kssssk......",
    ".....kkkk.......",
    "......dd........",
    "...ddddddd......",
    "..dkccccckd.....",
    "..dkcmccckd.....",
    "..lkcmccck......",
    "..lkmmcc........",
    "...lkkc.........",
    "...mmm..........",
    "...mmm..........",
    "...ll...........",
    "...ll...........",
    "...ll...........",
    "...bb...........",
    "...bb...........",
    "..b..b..........",
    "..b..b..........",
    "..b..b..........",
    "..b..b..........",
    "................",
    "................",
    "................",
    "................",
    "................",
]
# Weight on the front foot. Still the same drawing, a second pose, not a scale of the first.
STRIDE = [
    "................",
    "................",
    "......kkkk......",
    ".....kssssk.....",
    ".....kssssk.....",
    ".....khhssk.....",
    ".....kseesk.....",
    ".....kssssk.....",
    "......kkkk......",
    ".......dd.......",
    "....ddddddd.....",
    "...dkccccckd....",
    "...dkcmccckd....",
    "...lkcmccck.....",
    "...lkmmcc.......",
    "....lkkc........",
    "....mmm.........",
    "...mmm..........",
    "..ll..ll........",
    "..ll...l........",
    ".ll....l........",
    ".bb....b........",
    ".bb....b........",
    "bb......b.......",
    "b.......b.......",
    "b.......b.......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

POSES = (("idle", IDLE), ("stride", STRIDE))

def tiles_of(frame, rows):
    w, h, rgba, colours = grid_rgba(rows, PAL)
    if (w, h) != (16, 32):
        raise SystemExit("stand-in must be 16x32, got %sx%s" % (w, h))
    if len(colours) > 15:
        raise SystemExit("palette %s" % len(colours))
    out = []
    for ty in range(2):
        tile = bytearray(16 * 16 * 4)
        for y in range(16):
            src = ((ty * 16 + y) * w) * 4
            tile[y * 16 * 4:(y + 1) * 16 * 4] = rgba[src:src + 16 * 4]
        out.append({
            "key": "standin:wayfarer/%s/%d" % (frame, ty),
            "name": "wayfarer/%s/%d" % (frame, ty),
            "frame": frame,
            "w": 16, "h": 16, "rgba": tile,
        })
    return out

def build(outdir):
    tiles = []
    for name, rows in POSES:
        tiles.extend(tiles_of(name, rows))
    frames = walk_and_swing(IDLE, STRIDE)
    for name, rows, _smear in frames:
        tiles.extend(tiles_of(name, rows))
    info = pack(tiles, outdir)
    anim = {
        "standin": True,
        "timer": {"shown": "object+0x22", "count": "object+0x20"},
        "note": "Second half of the game's frame timer shows the smear cell. Replace standin: keys with the real cut.py key of that game frame's tile.",
        "byKey": anim_map(frames),
    }
    with open(os.path.join(outdir, "anim.json"), "w") as f:
        json.dump(anim, f, indent=1)
    info["standin"] = True
    info["frames"] = len(frames) + len(POSES)
    info["smears"] = sum(1 for _n, _r, s in frames if s)
    return info

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "skin", "standin")
    print(build(os.path.abspath(out)))
