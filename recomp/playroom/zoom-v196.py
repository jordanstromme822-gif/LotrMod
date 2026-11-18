"""Play Room v196: the zoom to the original small screen glides like a camera (Jordan, 2026-11-18: "make the zoom in feel
natural and more like a part of the game"; "It's when you go near edges").
Usage: zoom-v196.py playroom-v195.html out.html (page only, same engines and game file).

When the engine can't build the wide view (rotk_native_view(): near some map edges, menus over a level) it draws only the
middle 240x160 and the page used to snap to that part, stretched. Now:
- The picture always goes to the HD passes whole (no texture re-setup on every switch); the zoom is a camera rectangle
  that eases (smoothstep, ~0.35 s) between the whole view and the middle 240x160, applied in the last pass's viewport.
- While zooming in, the outer part comes from the last wide picture (frozen, it is only seen for those 0.35 s), so no
  black frame closes in. If there is no recent wide picture (game start, menus) it snaps like before.
- HUD band and height map follow the middle picture's HUD while the small screen shows (HudY from the HUD's real row).
- Impact effects, items, aura and trap lights use the same camera rectangle.
Works in 1-player, P2 and online (all draw through WideHost)."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

rep('''        let sx = 0, sy = 0, sw = w, sh = h;
        if (native && w >= 240 && h >= 160) { sx = (w - 240) >> 1; sy = (h - 160) >> 1; sw = 240; sh = 160; }
        if (this.fitDue !== false || this._gfx !== !!(window.__gfxLow && window.__gfxLow()) || this._sw !== sw || this._sh !== sh || this._fr !== !!window.__fullRes) { this._sw = sw; this._sh = sh; this._fr = !!window.__fullRes; this.fit(); }''',
'''        // v196: the small screen (native view) is a camera zoom that eases in and out instead of a snap.
        const full = native && w >= 240 && h >= 160, nowZ = performance.now(), dtZ = Math.min(100, nowZ - (this.zT || nowZ)); this.zT = nowZ;
        let src8 = this._u8, srcOff = base + this.d.pixels; const nB = w * h * 3;
        if (!full) {
          if (!this.zSaved || this.zSaved.length !== nB) this.zSaved = new Uint8Array(nB);
          this.zSaved.set(src8.subarray(srcOff, srcOff + nB)); this.zSavedT = nowZ; this.zW = w;
          this.zoom = w >= 240 && h >= 160 ? Math.max(0, (this.zoom || 0) - dtZ / 350) : 0;
        } else {
          const fresh = this.zSaved && this.zSaved.length === nB && this.zW === w && nowZ - (this.zSavedT || 0) < 500;
          if (!(this.zoom > 0) && !fresh) this.zoom = 1;   // nothing to zoom from (game start, menus): as before
          this.zoom = Math.min(1, (this.zoom || 0) + dtZ / 350);
          if (this.zoom < 1 && this.zSaved && this.zSaved.length === nB) {   // outer part from the last wide picture
            if (!this.zBuf || this.zBuf.length !== nB) this.zBuf = new Uint8Array(nB);
            const zb = this.zBuf, x0 = (w - 240) >> 1, y0 = (h - 160) >> 1; zb.set(this.zSaved);
            for (let y = 0; y < 160; y++) { const o = ((y0 + y) * w + x0) * 3; zb.set(src8.subarray(srcOff + o, srcOff + o + 720), o); }
            src8 = zb; srcOff = 0;
          }
        }
        const ez = (this.zoom || 0) * (this.zoom || 0) * (3 - 2 * (this.zoom || 0));
        const sx = ((w - 240) >> 1) * ez, sy = ((h - 160) >> 1) * ez, sw = w - (w - 240) * ez, sh = h - (h - 160) * ez;
        window.__hudB = full ? (h - 160) >> 1 : 0;   // rows under the HUD (the small screen's HUD sits in the middle)
        if (this.fitDue !== false || this._gfx !== !!(window.__gfxLow && window.__gfxLow()) || this._sw !== w || this._sh !== h || this._fr !== !!window.__fullRes) { this._sw = w; this._sh = h; this._fr = !!window.__fullRes; this.fit(); }''')
rep('''          if (window.__capF) window.__capF(this._u8, base + this.d.pixels, w, h);
          this.sharp(this._u8, base + this.d.pixels, w, sx, sy, sw, sh, dest, this.plain);''',
'''          if (window.__capF) window.__capF(this._u8, base + this.d.pixels, w, h);
          const dz = ez > 0 ? [dest[0] - sx * dest[2] / sw, dest[1] - sy * dest[3] / sh, w * dest[2] / sw, h * dest[3] / sh] : dest;   // v196: camera zoom
          this.sharp(src8, srcOff, w, 0, 0, w, h, dz, this.plain);''')
rep('''        for (let i = 0, s = base + this.d.pixels, t = 0; i < n; ++i, s += 3, t += 4) { dst[t] = src[s]; dst[t + 1] = src[s + 1]; dst[t + 2] = src[s + 2]; dst[t + 3] = 255; }''',
    '''        for (let i = 0, s = srcOff, t = 0; i < n; ++i, s += 3, t += 4) { dst[t] = src8[s]; dst[t + 1] = src8[s + 1]; dst[t + 2] = src8[s + 2]; dst[t + 3] = 255; }''')
rep('''        c.drawImage(this.buf, sx, sy, sw, sh, dest[0], dest[1], dest[2], dest[3]);''',
    '''        c.imageSmoothingEnabled = ez > 0 && ez < 1; c.drawImage(this.buf, sx, sy, sw, sh, dest[0], dest[1], dest[2], dest[3]);''')
# HUD band: the small screen's HUD is in the middle of the picture, not at its bottom
rep('h > 100 ? 1 - 34 / h : 2', 'h > 100 ? 1 - (34 + (window.__hudB || 0)) / h : 2', 2)
rep('h > 100 ? 34 : 0', 'h > 100 ? 34 + (window.__hudB || 0) : 0', 2)
open(out, 'w').write(t)
print('ok', len(t))
