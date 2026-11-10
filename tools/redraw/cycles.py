"""In-between frames for the wayfarer stand-in.

Four walked poses and four swings are shifts of the hand-drawn grids (whole pixels
only). The frames between them are smear frames: a one-pixel outline streak in the
direction of the motion, same palette, no blur. Eight frames each, so a 4-frame
game cycle can show a pose and then a smear while its own timer runs down.
"""

def shift_band(rows, y0, y1, dx):
    w = len(rows[0])
    out = list(rows)
    for y in range(y0, min(y1, len(rows))):
        buf = ["."] * w
        for x, ch in enumerate(rows[y]):
            nx = x + dx
            if ch != "." and 0 <= nx < w:
                buf[nx] = ch
        out[y] = "".join(buf)
    return out

def smear(rows, dx):
    w = len(rows[0])
    out = [list(r) for r in rows]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            nx = x + dx
            if 0 <= nx < w and out[y][nx] == ".":
                out[y][nx] = "k"
    return ["".join(r) for r in out]

def walk_and_swing(idle, stride):
    """Return (name, rows, smear) for 8 walk frames then 8 swing frames."""
    passing_r = shift_band(idle, 18, 32, 2)
    contact_l = shift_band(stride, 18, 32, -3)
    passing_l = shift_band(idle, 18, 32, -2)
    walk_poses = [stride, passing_r, contact_l, passing_l]
    walk_dx = [2, 2, -2, -2]
    cock = shift_band(idle, 10, 18, -2)
    strike = shift_band(idle, 10, 18, 3)
    follow = shift_band(idle, 10, 18, 1)
    swing_poses = [idle, cock, strike, follow]
    swing_dx = [-2, 3, -1, -2]
    frames = []
    for i, (pose, dx) in enumerate(zip(walk_poses, walk_dx)):
        frames.append(("walk/%d" % (i * 2), pose, False))
        frames.append(("walk/%d" % (i * 2 + 1), smear(pose, dx), True))
    for i, (pose, dx) in enumerate(zip(swing_poses, swing_dx)):
        frames.append(("swing/%d" % (i * 2), pose, False))
        frames.append(("swing/%d" % (i * 2 + 1), smear(pose, dx), True))
    return frames

def anim_map(frames):
    """Pose key -> [pose key, smear key] for each tile row. Smear entries are not keys themselves."""
    by = {}
    tiles = 2
    i = 0
    while i < len(frames):
        name, _rows, is_smear = frames[i]
        if is_smear:
            i += 1
            continue
        if i + 1 >= len(frames) or not frames[i + 1][2]:
            i += 1
            continue
        smear_name = frames[i + 1][0]
        for ty in range(tiles):
            key = "standin:wayfarer/%s/%d" % (name, ty)
            alt = "standin:wayfarer/%s/%d" % (smear_name, ty)
            by[key] = [key, alt]
        i += 2
    return by
