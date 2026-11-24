# Play Room v258: the pillar torches finished (Jordan, 2026-11-24: "placement looks good go ahead and finish it" /
# "like add the mount and angle them and the details and such"). Each torch now sits in an iron wall sconce: a riveted
# plate on the pillar face, a short arm and a ring holding the torch, which leans out from the face it is mounted on
# (left face leans left, right face leans right). The flame stays upright (fire rises). Soot darkens the stone above
# every torch, lit or not. Lit torches flicker, glow and give off thin smoke; the smouldering one shows a pulsing
# cherry-red ember in the torch head and more smoke. Out in the morning, unlit charred heads by day.
# Sprite data: tools in recomp/playroom/torch-mounted-v258.json (built by the torch compose script: the game's own
# Hornburg torch flame and handle from level 46, iron in the game's dark-grey ramp).
# Replaces the v257 block. Usage: python3 torches-v258.py in.html torch-mounted-v258.json out.html
import json, re, sys
p, data, out = sys.argv[1], sys.argv[2], sys.argv[3]; s = open(p, encoding='utf-8').read()
MOUNT = json.load(open(data))
a = s.index('  // v257 torches on some pillars at night')
b = s.index('  // Graphics High/Low (2026-11-12)', a)
block = '''  // v258 torches in iron sconces on some pillars at night (see recomp/playroom/torches-v258.py). Level -> [map x, map y of
  // the wall plate, 1 = lit at night / 2 = smouldering, "L" = on a left face leaning left / "R" = right face leaning right].
  (() => {
    const MOUNT = ''' + json.dumps(MOUNT, separators=(',', ':')) + ''';
    const TORCHES = { 112: [[340, 372, 1, "L"], [515, 372, 1, "L"], [769, 372, 2, "L"]] };
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
      const mul = (X, Y, k) => { const i = at(X, Y); if (i < 0) return; keep(i); heap[i] *= k; heap[i + 1] *= k; heap[i + 2] *= k; };
      const glow = (X, Y, r, g, b, rad, k) => { for (let y = -rad; y <= rad; y++) for (let x = -rad; x <= rad; x++) {
        const d = (x * x + y * y * 1.69) / (rad * rad * 0.36); if (d > 2.8) continue; const L = Math.exp(-d) * k, i = at(X + x, Y + y); if (i < 0) continue; keep(i);
        heap[i] = Math.min(255, heap[i] * (1 + L * r * 2.2) + L * r * 40); heap[i + 1] = Math.min(255, heap[i + 1] * (1 + L * g * 2.2) + L * g * 40); heap[i + 2] = Math.min(255, heap[i + 2] * (1 + L * b * 2.2) + L * b * 40); } };
      list.forEach(([tx, ty, kind, side], n) => {
        const V = MOUNT[side], X = tx + ox, Y = ty + oy;
        if (X < sx - 40 || X > sx + w + 40 || Y < sy - 80 || Y > sy + h + 40) return;
        const on = lit, fl = 0.85 + 0.15 * Math.sin(now * 13 + n * 2.1) * Math.sin(now * 7.3 + n);
        const [fx, fy] = V.flame, [ex, ey] = V.ember;
        // soot on the stone above the torch head (always there: the torch has burned before)
        for (const [x, y, k] of V.soot) mul(X + x, Y + y, k / 100);
        // smoke: puffs rise from the flame top (lit) or the ember (smouldering), in map pixels so they stay put as the camera moves
        const S = smoke[lv + ':' + n] || (smoke[lv + ':' + n] = { p: [], t: 0 });
        if (on) { S.t -= dt; if (S.t <= 0) { S.t = kind === 2 ? 0.16 : 0.26; S.p.push({ x: tx + (kind === 2 ? ex : fx) + (Math.random() - 0.5), y: ty + (kind === 2 ? ey - 3 : fy - 8), a: 0, vx: (Math.random() - 0.4) * 1.2 }); } }
        for (const q of S.p) { q.a += dt; q.y -= dt * 12; q.x += dt * (q.vx + 2.2 * Math.sin(q.a * 2.4 + n)); }
        S.p = S.p.filter((q) => q.a < 3.4);
        const base = ty + (kind === 2 ? ey : fy);
        for (const q of S.p) { const t = q.a / 3.4, rad = 0.8 + 3.6 * t, al = Math.round((1 - t) ** 1.4 * (kind === 2 ? 0.66 : 0.5) * 6) / 6;
          if (al <= 0) continue; const warm = Math.max(0, 1 - (base - q.y) / 25), r = 104 * (1 - warm) + 176 * warm, g = 101 * (1 - warm) + 112 * warm, b = 100 * (1 - warm) + 80 * warm;
          for (let y = -Math.ceil(rad); y <= Math.ceil(rad); y++) for (let x = -Math.ceil(rad); x <= Math.ceil(rad); x++) if (x * x + y * y <= rad * rad) {
            const i = at(q.x + ox + x, q.y + oy + y); if (i < 0) continue; const lum = heap[i] * 0.3 + heap[i + 1] * 0.59 + heap[i + 2] * 0.11, d = lum > 115 ? 0.55 : 1.45;   // a veil: darker over lit stone, lighter over the dark sky
            put(q.x + ox + x, q.y + oy + y, r * d, g * d, b * d, al * (1 - (x * x + y * y) / (rad * rad + 1) * 0.5)); } }
        if (on && kind === 1) glow(X + fx, Y + fy + 3, 1.0, 0.32, 0.06, 24, 0.55 * fl);
        if (on && kind === 2) glow(X + ex, Y + ey - 1, 1.0, 0.12, 0.03, 16, 1.0 * (0.75 + 0.25 * Math.sin(now * 2.2 + n)));
        // sconce, handle and flame (or the charred head when it is out)
        for (const [dx, dy, r, g, b, part] of V.px) {
          if (part === 0) {
            if (on && kind === 1) { const k = dy < fy - 1 ? fl : 1; put(X + dx + (dy < fy - 3 && Math.sin(now * 9 + n) > 0.6 ? 1 : 0), Y + dy, r * k + 20 * (1 - k), g * k, b * k, 1); }
            else if (dy >= ey - 4) put(X + dx, Y + dy, 24, 20, 18, 1);
            continue;
          }
          put(X + dx, Y + dy, r, g, b, 1);
        }
        if (on && kind === 2) { const k = 0.75 + 0.25 * Math.sin(now * 2.2 + n);
          for (const [dx, dy, r, g, b] of [[0, -3, 150, 26, 10], [0, -2, 255, 90, 30], [-1, -1, 220, 40, 14], [1, -1, 235, 50, 16], [0, -1, 255, 130 * k, 50 * k]]) put(X + ex + dx, Y + ey + dy, r, g, b, 1); }
      });
      if (!undo.length) return null;
      return () => { for (let j = 0; j < undo.length; j += 4) { const i = undo[j]; heap[i] = undo[j + 1]; heap[i + 1] = undo[j + 2]; heap[i + 2] = undo[j + 3]; } };
    };
  })();
'''
s = s[:a] + block + s[b:]
s = s.replace('// v257 torches\n', '// v257 torches (v258 sconces)\n')
open(out, 'w', encoding='utf-8').write(s); print('ok v258 torches')
