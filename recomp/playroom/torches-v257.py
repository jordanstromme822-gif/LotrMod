# Play Room v257: torches on some pillars at night (Jordan, 2026-11-22: "could we add torches on the pillars that
# activate at night or have a red cherry glow with smoke coming off?" ... "Just some of them"; mock-up OK'd 2026-11-24).
# The torch is the game's own Hornburg wall torch (level 46 map art, rows 190-216 x 429-437), fixed to the pillar
# face under the capital. Lit at dusk and through the night, out in the morning (day cycle from v247). Lit torches
# flicker and give off a thin trail of smoke; a smouldering one shows a pulsing cherry-red ember and more smoke.
# Painted into the game picture just before it is uploaded (and put back right after, so the engine's own rows are
# untouched), so the lighting passes treat the flame as a real light, and every mode (1 player, P2, online) shows it.
# Usage: python3 torches-v257.py in.html sprite.json out.html
import json, sys
p, spr, out = sys.argv[1], sys.argv[2], sys.argv[3]; s = open(p, encoding='utf-8').read()
SPR = json.load(open(spr))
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)

rep('''        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RGB, gl.UNSIGNED_BYTE, heap, off);
        gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0); gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0);
        frame++;
''', '''        let fxUndo = null; try { fxUndo = window.__torchFX ? window.__torchFX(heap, off, stride, sx, sy, w, h) : null; } catch (e) { fxUndo = null; }   // v257 torches
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RGB, gl.UNSIGNED_BYTE, heap, off);
        if (fxUndo) fxUndo();
        gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0); gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0);
        frame++;
''')

rep('''  // Graphics High/Low (2026-11-12)''', '''  // v257 torches on some pillars at night (see recomp/playroom/torches-v257.py). Level -> [map x, map y of the torch
  // top, 1 = lit at night / 2 = smouldering]. Map pixels, the same as the hero's x/y.
  (() => {
    const SPR = ''' + json.dumps(SPR, separators=(',', ':')) + ''';
    const TORCHES = { 112: [[339, 340, 1], [513, 340, 1], [767, 340, 2]] };
    const smoke = {}; let lastT = 0;
    window.__torchFX = (heap, off, stride, sx, sy, w, h) => {
      const M = window.__wideM; if (!M || !M._rotk_iwram) return null;
      const mp = window.__mp, ib = mp && mp.online && mp.iwram ? mp.iwram() : M._rotk_iwram(), H8 = M.HEAPU8;
      if (H8[ib + 0x41B0] !== 1) return null;
      const lv = H8[ib + 0x41F8], list = TORCHES[lv]; if (!list) return null;
      const dv = new DataView(H8.buffer), cx = dv.getInt32(ib + 0x20F8, true), cy = dv.getInt32(ib + 0x20FC, true);
      const ox = (stride - 240) / 2 - cx, oy = (h - 160) / 2 - cy;
      const pw = LIGHT_LOOKS.phaseW(), lit = pw[2] + pw[3] > 0.5;   // dusk and night
      const now = performance.now() / 1000, dt = Math.min(0.1, lastT ? now - lastT : 0); lastT = now;
      const undo = [], seen = new Set();
      const at = (X, Y) => { X = Math.round(X); Y = Math.round(Y); if (X < sx || X >= sx + w || Y < sy || Y >= sy + h) return -1; return heap.length > off + (Y * stride + X) * 3 + 2 ? off + (Y * stride + X) * 3 : -1; };
      const keep = (i) => { if (!seen.has(i)) { seen.add(i); undo.push(i, heap[i], heap[i + 1], heap[i + 2]); } };
      const put = (X, Y, r, g, b, a) => { const i = at(X, Y); if (i < 0) return; keep(i);
        heap[i] = Math.min(255, heap[i] * (1 - a) + r * a); heap[i + 1] = Math.min(255, heap[i + 1] * (1 - a) + g * a); heap[i + 2] = Math.min(255, heap[i + 2] * (1 - a) + b * a); };
      const glow = (X, Y, r, g, b, rad, k) => { for (let y = -rad; y <= rad; y++) for (let x = -rad; x <= rad; x++) {
        const d = (x * x + y * y * 1.69) / (rad * rad * 0.36); if (d > 2.8) continue; const L = Math.exp(-d) * k, i = at(X + x, Y + y); if (i < 0) continue; keep(i);
        heap[i] = Math.min(255, heap[i] * (1 + L * r * 2.2) + L * r * 40); heap[i + 1] = Math.min(255, heap[i + 1] * (1 + L * g * 2.2) + L * g * 40); heap[i + 2] = Math.min(255, heap[i + 2] * (1 + L * b * 2.2) + L * b * 40); } };
      list.forEach(([tx, ty, kind], n) => {
        const X = tx + ox, Y = ty + oy;
        if (X < sx - 40 || X > sx + w + 40 || Y < sy - 80 || Y > sy + h + 40) return;
        const on = lit, fl = 0.85 + 0.15 * Math.sin(now * 13 + n * 2.1) * Math.sin(now * 7.3 + n);
        // smoke: puffs rise from the flame (lit) or the ember (smouldering), in map pixels so they stay put as the camera moves
        const S = smoke[lv + ':' + n] || (smoke[lv + ':' + n] = { p: [], t: 0 });
        if (on) { S.t -= dt; if (S.t <= 0) { S.t = kind === 2 ? 0.16 : 0.26; S.p.push({ x: tx + (Math.random() - 0.5), y: ty + (kind === 2 ? 9 : 1), a: 0, vx: (Math.random() - 0.4) * 1.2 }); } }
        for (const q of S.p) { q.a += dt; q.y -= dt * 12; q.x += dt * (q.vx + 2.2 * Math.sin(q.a * 2.4 + n)); }
        S.p = S.p.filter((q) => q.a < 3.4);
        for (const q of S.p) { const t = q.a / 3.4, rad = 0.8 + 3.6 * t, al = Math.round((1 - t) ** 1.4 * (kind === 2 ? 0.66 : 0.5) * 6) / 6;
          if (al <= 0) continue; const warm = Math.max(0, 1 - (ty - q.y) / 25), r = 104 * (1 - warm) + 176 * warm, g = 101 * (1 - warm) + 112 * warm, b = 100 * (1 - warm) + 80 * warm;
          for (let y = -Math.ceil(rad); y <= Math.ceil(rad); y++) for (let x = -Math.ceil(rad); x <= Math.ceil(rad); x++) if (x * x + y * y <= rad * rad) {
            const i = at(q.x + ox + x, q.y + oy + y); if (i < 0) continue; const lum = heap[i] * 0.3 + heap[i + 1] * 0.59 + heap[i + 2] * 0.11, d = lum > 115 ? 0.55 : 1.45;   // a veil: darker over lit stone, lighter over the dark sky
            put(q.x + ox + x, q.y + oy + y, r * d, g * d, b * d, al * (1 - (x * x + y * y) / (rad * rad + 1) * 0.5)); } }
        // the torch itself
        if (on && kind === 1) glow(X, Y + 8, 1.0, 0.32, 0.06, 28, 0.85 * fl);
        if (on && kind === 2) glow(X, Y + 11, 1.0, 0.12, 0.03, 16, 1.0 * (0.75 + 0.25 * Math.sin(now * 2.2 + n)));
        for (const [dx, dy, r, g, b, part] of SPR) {
          if (part === 0 && !(on && kind === 1)) { if (dy >= 9) put(X + dx, Y + dy, 22, 18, 16, 1); continue; }
          if (part === 0) { const k = dy < 6 ? fl : 1; put(X + dx + (dy < 5 && Math.sin(now * 9 + n) > 0.6 ? 1 : 0), Y + dy, r * k + 20 * (1 - k), g * k, b * k, 1); }
          else put(X + dx, Y + dy, r, g, b, 1);
        }
        for (let x = -2; x <= 2; x++) { put(X + x, Y + 26, 26, 24, 22, 1); put(X + x, Y + 27, 26, 24, 22, 1); }
        if (on && kind === 2) { const k = 0.75 + 0.25 * Math.sin(now * 2.2 + n);
          for (const [dx, dy, r, g, b] of [[0, 9, 150, 26, 10], [0, 10, 255, 76, 24], [-1, 11, 220, 40, 14], [1, 11, 235, 50, 16], [0, 11, 255, 120 * k, 40 * k], [0, 12, 255, 86, 28], [-1, 12, 170, 26, 10], [1, 12, 190, 30, 12], [0, 13, 140, 22, 10]]) put(X + dx, Y + dy, r, g, b, 1); }
      });
      if (!undo.length) return null;
      return () => { for (let j = 0; j < undo.length; j += 4) { const i = undo[j]; heap[i] = undo[j + 1]; heap[i + 1] = undo[j + 2]; heap[i + 2] = undo[j + 3]; } };
    };
  })();
  // Graphics High/Low (2026-11-12)''')
open(out, 'w', encoding='utf-8').write(s); print('ok v257 torches')
