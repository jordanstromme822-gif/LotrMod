# Fangorn night fix (Jordan, 2026-11-17: "At night the lights in fangore forest go wild").
# At night the mood light map turns bright, saturated, contrasting pixels into coloured light pools (torches, fires,
# spells). Fangorn's lime-green leaf highlights pass all three tests, so every lit leaf became a green lamp, and as the
# camera scrolls and the trees sway the pools pop on and off. Leaves are green-dominant (g well above r and b); flames
# (r >= g), spells (blue/white) and lava are not, so green-dominant pixels no longer emit.
# Usage: python3 foliage_light.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
old = "  float b = smoothstep(Thr, Thr + 0.14, mx) * smoothstep(0.45, 0.75, sat) * smoothstep(0.2, 0.4, length(c - sur)) * (1.0 - step(HudY, uv.y));"
new = ("  float leaf = smoothstep(0.06, 0.18, c.g - c.r) * smoothstep(0.04, 0.16, c.g - c.b);   // leaves and grass: green-dominant, never a light\\n\" +\n    \""
       "  float b = smoothstep(Thr, Thr + 0.14, mx) * smoothstep(0.45, 0.75, sat) * smoothstep(0.2, 0.4, length(c - sur)) * (1.0 - step(HudY, uv.y)) * (1.0 - leaf);")
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(out, "w").write(s); print("ok foliage")
