# Day and night cycle (Jordan, 2026-11-10: "we could do day and night cycles every 4 minutes"): outdoor levels spend
# 4 minutes in day and 4 in night, with a 30 second dusk and dawn. Helm's Deep's night is its misty v159 mood and its
# day is the Fortress look. Mordor, lava, wasteland, caves and dwarf halls keep their fixed mood.
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
rep("    return { looks, forLevel: (n) => looks[byLevel[n]] || looks.level, names: byLevel };",
"""    // Day and night: the clock decides (so two players see the same sky). nightness 0 = day, 1 = night.
    const NIGHT = { Night: 0.9, NightTint: [0.32, 0.38, 0.52], TorchK: 1.0, Mist: 0.45, MistCol: [0.36, 0.42, 0.52], AO: 0.4, Sun: 0.0, Vig: 0.4, GlowK: 0.4 };   // less of the day glow: sunlit grass would glow warm
    const FIXED = { Mordor: 1, Lava: 1, Wasteland: 1, Caves: 1, "Dwarf halls": 1 };
    const nightness = () => {
      if (typeof window.__rotkNightForce === "number") return window.__rotkNightForce;
      const T = 480, h = T / 2, r = 30, t = (Date.now() / 1000) % T, up = (x) => Math.min(1, Math.max(0, x / r));
      let n = t < r / 2 ? 1 - up(t + r / 2) : t < h + r / 2 ? up(t - (h - r / 2)) : 1 - up(t - (T - r / 2));
      return n * n * (3 - 2 * n);
    };
    const blend = (a, b, k) => { const o = {}; for (const key in a) { const x = a[key], y = key in b ? b[key] : x; o[key] = Array.isArray(x) ? x.map((v, j) => v + (y[j] - v) * k) : x + (y - x) * k; } return o; };
    const cycled = (n) => {
      const g = byLevel[n], day = g === "Helm's Deep" ? looks.Fortress : looks[g] || looks.level;
      if (FIXED[g]) return looks[g];
      const k = nightness(); if (k <= 0) return day;
      return blend(day, g === "Helm's Deep" ? looks["Helm's Deep"] : NIGHT, k);
    };
    return { looks, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, names: byLevel };""")
rep("      if (st === 1) window.__rotkLook = LIGHT_LOOKS.forLevel(lv);", "      if (st === 1) window.__rotkLook = LIGHT_LOOKS.cycled(lv);")
# Light sources must stand out from what is around them (flames, spells), so bright sunlit ground (golden grass, sand,
# pale stone) no longer counts as a light and no longer cancels the night.
rep("float sat = (mx - mn) / max(mx, 0.001);\\n\" +\n    \"  float b = smoothstep(Thr, Thr + 0.14, mx) * smoothstep(0.45, 0.75, sat)",
    "float sat = (mx - mn) / max(mx, 0.001);\\n\" +\n    \"  vec3 sur = (texture(Texture, uv + SrcPx * vec2(7.0, 0.0)).rgb + texture(Texture, uv - SrcPx * vec2(7.0, 0.0)).rgb + texture(Texture, uv + SrcPx * vec2(0.0, 7.0)).rgb + texture(Texture, uv - SrcPx * vec2(0.0, 7.0)).rgb) * 0.25;\\n\" +\n    \"  float b = smoothstep(Thr, Thr + 0.14, mx) * smoothstep(0.45, 0.75, sat) * smoothstep(0.2, 0.4, length(c - sur))")
open(out, "w").write(s); print("patched")
