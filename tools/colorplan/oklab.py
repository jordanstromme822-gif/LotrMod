"""OKLab / OKLCH helpers and GBA 15-bit colour conversion (no dependencies but numpy)."""
import numpy as np, math

def srgb_to_lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255.0

def rgb_to_oklab(rgb):
    r, g, b = np.moveaxis(srgb_to_lin(rgb), -1, 0)
    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return np.stack([0.2104542553*l + 0.7936177850*m - 0.0040720468*s,
                     1.9779984951*l - 2.4285922050*m + 0.4505937099*s,
                     0.0259040371*l + 0.7827717662*m - 0.8086757660*s], -1)

def oklab_to_rgb(lab):
    L, a, b = np.moveaxis(np.asarray(lab, float), -1, 0)
    l = (L + 0.3963377774*a + 0.2158037573*b) ** 3
    m = (L - 0.1055613458*a - 0.0638541728*b) ** 3
    s = (L - 0.0894841775*a - 1.2914855480*b) ** 3
    r = 4.0767416621*l - 3.3077115913*m + 0.2309699292*s
    g = -1.2684380046*l + 2.6097574011*m - 0.3413193965*s
    bb = -0.0041960863*l - 0.7034186147*m + 1.7076147010*s
    return lin_to_srgb(np.stack([r, g, bb], -1))

def lch(L, C, h_deg):
    """OKLCH -> sRGB 0..255, chroma reduced until it fits the sRGB gamut."""
    for _ in range(40):
        rgb = oklab_to_rgb([L, C * math.cos(math.radians(h_deg)), C * math.sin(math.radians(h_deg))])
        lin_ok = True
        # check gamut before clipping
        a, b = C * math.cos(math.radians(h_deg)), C * math.sin(math.radians(h_deg))
        l_ = (L + 0.3963377774*a + 0.2158037573*b) ** 3
        m_ = (L - 0.1055613458*a - 0.0638541728*b) ** 3
        s_ = (L - 0.0894841775*a - 1.2914855480*b) ** 3
        lin = [4.0767416621*l_ - 3.3077115913*m_ + 0.2309699292*s_,
               -1.2684380046*l_ + 2.6097574011*m_ - 0.3413193965*s_,
               -0.0041960863*l_ - 0.7034186147*m_ + 1.7076147010*s_]
        if min(lin) >= -1e-4 and max(lin) <= 1 + 1e-4: return rgb
        C *= 0.92
    return rgb

def to_lch(rgb):
    L, a, b = rgb_to_oklab(rgb)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360

def gba(rgb):
    """Snap to the GBA's 5-bit-per-channel colours; returns (rgb888, bgr555)."""
    r, g, b = [int(round(min(255, max(0, v)) / 255 * 31)) for v in rgb]
    return (r << 3, g << 3, b << 3), r | (g << 5) | (b << 10)

def from555(v):
    return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3)
