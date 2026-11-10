"""Colour plan for the Return of the King redraw.

Every material is a ramp: value t (0 = deepest shadow, 1 = top highlight) -> OKLCH colour.
Rules baked in (see docs/color-plan.md):
  * value first: the game's own lightness order is kept, so shapes read the same;
  * hue shift: shadows slide toward cool blue-violet, highlights toward warm yellow
    (the light is warm sun/torch, the fill is cool sky);
  * chroma peaks in the mid tones and falls off in deep shadow and top highlight;
  * environments live in a narrower, lower-chroma band; heroes get the full value
    range and the strongest chroma, so they are always the focal point.
"""
import math
from oklab import lch, to_lch, gba

COOL, WARM = 285.0, 80.0          # shadow hue and highlight hue (OKLCH degrees)

def _toward(h, target, k):
    d = ((target - h + 180) % 360) - 180
    return (h + d * k) % 360

class Ramp:
    def __init__(self, name, hue, cmax, lrange, cool=0.55, warm=0.45, cmin=0.004, role='env'):
        self.name, self.hue, self.cmax, self.lrange = name, hue, cmax, lrange
        self.cool, self.warm, self.cmin, self.role = cool, warm, cmin, role
    def __call__(self, t):
        t = min(1.0, max(0.0, t))
        L = self.lrange[0] + (self.lrange[1] - self.lrange[0]) * t
        if t < 0.5: h = _toward(self.hue, COOL, self.cool * (0.5 - t) * 2)
        else:       h = _toward(self.hue, WARM, self.warm * (t - 0.5) * 2)
        C = self.cmin + (self.cmax - self.cmin) * math.sin(math.pi * (0.18 + 0.72 * t)) ** 0.9
        return lch(L, C, h)

ENV = (0.15, 0.84)                 # environment value band (OKLab L)
HERO = (0.13, 0.94)                # hero value band

RAMPS = {
    # environment
    'stone':      Ramp('stone', 75, 0.034, ENV, cool=1.0, warm=0.35),
    'stone-dark': Ramp('stone-dark', 285, 0.030, ENV, cool=0.3, warm=0.7),
    'moss':       Ramp('moss', 128, 0.060, ENV, cool=0.35, warm=0.4),
    'slate':      Ramp('slate', 235, 0.040, ENV, cool=0.3, warm=0.5),
    'earth':      Ramp('earth', 60, 0.060, ENV, cool=0.45, warm=0.35),
    'grass':      Ramp('grass', 135, 0.110, ENV, cool=0.4, warm=0.45),
    'foliage':    Ramp('foliage', 140, 0.120, ENV, cool=0.45, warm=0.5),
    'bark':       Ramp('bark', 55, 0.050, ENV, cool=0.5, warm=0.3),
    'water':      Ramp('water', 215, 0.090, ENV, cool=0.3, warm=0.25),
    'snow':       Ramp('snow', 240, 0.030, (0.30, 0.96), cool=0.4, warm=0.5),
    'lava':       Ramp('lava', 40, 0.190, (0.25, 0.92), cool=0.25, warm=0.9),
    'ash':        Ramp('ash', 30, 0.025, ENV, cool=0.5, warm=0.2),
    # heroes
    'steel':      Ramp('steel', 275, 0.018, HERO, cool=0.6, warm=0.95, role='hero'),
    'ranger':     Ramp('ranger', 255, 0.095, HERO, cool=0.3, warm=0.1, role='hero'),
    'skin':       Ramp('skin', 50, 0.085, (0.40, 0.92), cool=-0.25, warm=0.35, role='hero'),
    'leather':    Ramp('leather', 42, 0.120, HERO, cool=0.25, warm=0.3, role='hero'),
    'wizard':     Ramp('wizard', 95, 0.030, HERO, cool=0.5, warm=0.6, role='hero'),
    'elf-green':  Ramp('elf-green', 140, 0.100, HERO, cool=0.4, warm=0.55, role='hero'),
    'dwarf-red':  Ramp('dwarf-red', 30, 0.130, HERO, cool=0.3, warm=0.4, role='hero'),
    'gold':       Ramp('gold', 85, 0.120, HERO, cool=0.3, warm=0.5, role='hero'),
}

def recolor(rgb, ramp, lmap=None):
    """Map one original colour onto a ramp by its own lightness."""
    L, C, h = to_lch(rgb)
    t = L if lmap is None else lmap(L)
    return gba(RAMPS[ramp](t))[0]

def auto_material(rgb):
    """Rough material guess for environment colours (used for palettes not hand-tagged)."""
    L, C, h = to_lch(rgb)
    if C < 0.025: return 'stone'
    if 95 <= h < 175: return 'moss'
    if 175 <= h < 290: return 'stone-dark'
    return 'earth'
