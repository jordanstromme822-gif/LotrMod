  // v255 Isengard's mountains (tools/region/mountains.py): ridges grown from the game's own mountain levels, drawn over
  // the game's picture wherever the map shows its 'key' tile (one colour no region tile uses). Heroes, enemies and
  // effects cover the key, so they stay in front of the rock. The map spot under each mountain spot is blocked.
  // Works in 1-player, P2 and online (all draw through WideHost). Data: maps/x/M51.bin (zlib), rock and ground atlases.
  (() => {
    const O = __MOUNTAINS__;
    let RK = null, GR = null, SH = null, W8 = 0, H8 = 0, rock = null, ground = null, plain = null, PW = 0, PH = 0, face = null, FW = 0, FH = 0, last = [0, 0], miss = 0, dbg = {};
    const img = (url, cb) => { try { const im = new Image(); im.onload = () => { try { const c = document.createElement("canvas"); c.width = im.width; c.height = im.height; const x = c.getContext("2d"); x.drawImage(im, 0, 0); cb(x.getImageData(0, 0, im.width, im.height).data, im.width); } catch (e) {} }; im.src = url; } catch (e) {} };
    // atlases: 8x8 tiles in rows of 64; tile i -> flat arrays (rock: rgba 256 bytes, ground: 64 palette indices)
    img(O.rock, (d, w) => { const n = O.nRock, a = new Uint8Array(n * 256);
      for (let i = 0; i < n; i++) for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { const s = (((i >> 6) * 8 + y) * w + (i & 63) * 8 + x) * 4, t = i * 256 + (y * 8 + x) * 4; a[t] = d[s]; a[t + 1] = d[s + 1]; a[t + 2] = d[s + 2]; a[t + 3] = d[s + 3]; }
      rock = a; });
    img(O.ground, (d, w) => { const n = O.nGround, a = new Uint8Array(n * 64);
      for (let i = 0; i < n; i++) for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) a[i * 64 + y * 8 + x] = d[(((i >> 6) * 8 + y) * w + (i & 63) * 8 + x) * 4] & 15;
      ground = a; });
    // v257 the drop (tools/region/drop.py): ground 0xFFFF spots show the far valley below, scrolled at half speed, with the
    // earth bank hung under the edge (shade = drop spots above, 255 none)
    if (O.plain) img(O.plain, (d, w) => { PW = w; PH = d.length / 4 / w; plain = d; });
    if (O.face) img(O.face, (d, w) => { FW = w; FH = d.length / 4 / w; face = d; });
    // the flood (tools/region/water.py): ground 0xFFFE spots are Isengard's drowned pits and pools, the game's own 32 px
    // water scrolled along its ripples with passing glints; steam rises from O.vents
    let water = null; if (O.water) img(O.water, (d) => { water = d; });
    (async () => { try {
      const r = await fetch(O.bin); const ds = r.body.pipeThrough(new DecompressionStream("deflate"));
      const b = new Uint8Array(await new Response(ds).arrayBuffer());
      if (b[0] !== 77 || b[1] !== 84 || b[2] !== 78 || b[3] !== 49) return;
      W8 = b[4] | b[5] << 8; H8 = b[6] | b[7] << 8; const n = W8 * H8;
      const al = new Uint8Array(b.buffer.slice(8)); RK = new Uint16Array(al.buffer, 0, n); GR = new Uint16Array(al.buffer, 2 * n, n); SH = al.subarray(4 * n, 5 * n);
    } catch (e) { dbg.err = String(e); } })();
    const RG = O.rows;
    const conv = (c) => [(c & 31) << 3 | (c & 31) >> 2, (c >> 5 & 31) << 3 | (c >> 5 & 31) >> 2, (c >> 10 & 31) << 3 | (c >> 10 & 31) >> 2];
    window.__mountainsDbg = { info: () => Object.assign({ data: !!RK, rock: !!rock, ground: !!ground, plain: !!plain, face: !!face, last, miss }, dbg) };
    window.__mountains = (u8, off, w, h) => {
      const M = window.__wideM; if (!M || !RK || !rock || !ground || (O.plain && (!plain || !face)) || (O.water && !water) || !M._rotk_iwram || !M._rotk_ewram || w < 240 || h < 160) return;
      // the shown game: online = this page's player, otherwise game 0; 2-player engines keep the palette RAM 0x48000
      // after the game's EWRAM (rotk_pal only knows the 1-player game)
      const mp = window.__mp, link = !!(M._rotk_link_on && M._rotk_link_on()), on = !!(mp && mp.online && mp.ewram);
      const H8b = M.HEAPU8, iw = on ? mp.iwram() : M._rotk_iwram(), ew0 = on ? mp.ewram() : M._rotk_ewram();
      const r32 = (a) => (H8b[iw + a] | H8b[iw + a + 1] << 8 | H8b[iw + a + 2] << 16 | H8b[iw + a + 3] << 24);
      if (H8b[iw + 0x4174] !== O.level || r32(0x41B0) !== 1) return;
      const pa = link || on || !M._rotk_pal ? ew0 + 0x48000 : M._rotk_pal();
      if (pa & 1) return;
      const pal = new Uint16Array(H8b.buffer, pa, 256);
      const K = conv(pal[O.key[0] * 16 + O.key[1]]), k0 = K[0], k1 = K[1], k2 = K[2];
      const isKey = (x, y) => { const k = off + (y * w + x) * 3; return u8[k] === k0 && u8[k + 1] === k1 && u8[k + 2] === k2; };
      const ex = r32(0x20F8) - ((w - 240) >> 1), ey = r32(0x20FC) - ((h - 160) >> 1);   // camera (0x030020F8/FC, as the hit effects use): level px of the picture's (0, 0)
      window.__mtnView = { x: ex + (w >> 1), y: ey + (h >> 1), t: performance.now() };   // the ambience's listener
      const inM = (px, py) => { const sx = px >> 3, sy = py >> 3; return sx >= 0 && sy >= 0 && sx < W8 && sy < H8 && GR[sy * W8 + sx] !== 0; };
      // samples: every 6th pixel on a coarse grid; does the picture's key agree with the map's mountain spots?
      const S = []; let anyKey = false, anyM = false;
      for (let y = 3; y < h; y += 9) for (let x = 2; x < w; x += 9) { const kk = isKey(x, y); S.push(x, y, kk ? 1 : 0); if (kk) anyKey = true; }
      for (let y = -16; y < h + 16 && !anyM; y += 8) for (let x = -16; x < w + 16; x += 8) if (inM(ex + x, ey + y)) { anyM = true; break; }
      if (!anyKey && !anyM) return;
      // holes = key showing where the layer would draw no mountain (black on screen). Mountain spots without the key are
      // fine (a hero, an enemy or the 2-player HUD in front) and only break ties.
      const holes = (fx, fy) => { let b = 0; for (let i = 0; i < S.length; i += 3) if (S[i + 2] && !inM(fx + S[i], fy + S[i + 1])) b++; return b; };
      const cover = (fx, fy) => { let b = 0; for (let i = 0; i < S.length; i += 3) if (!S[i + 2] && inM(fx + S[i], fy + S[i + 1])) b++; return b; };
      // the camera is usually exact; while scrolling the picture can lag it a little: then the last offset and their
      // neighbours, the whole +-12 square only if none fits
      let bx = 0, by = 0, best = holes(ex, ey) * 1e4;
      if (best > 0) {
        best += cover(ex, ey);
        const tryAt = (dx, dy) => { const hh = holes(ex + dx, ey + dy); if (hh * 1e4 > best) return; const s = hh * 1e4 + cover(ex + dx, ey + dy); if (s < best) { best = s; bx = dx; by = dy; } };
        tryAt(last[0], last[1]);
        for (const [cx, cy] of [[0, 0], [last[0], last[1]]]) for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) tryAt(cx + dx, cy + dy);
        if (best >= 1e4) { for (let dy = -12; dy <= 12; dy++) for (let dx = -12; dx <= 12; dx++) tryAt(dx, dy); if (best >= 1e4) miss++; }
      }
      last = [bx, by];
      const fx = ex + bx, fy = ey + by; dbg = { best, bx, by, ex, ey, w, h, K: [k0, k1, k2] };
      let tags = null; try { const sp = M._rotk_skin_slot ? M._rotk_skin_slot(window.GbrHost.front) : 0; if (sp) tags = new Uint32Array(M.HEAPU8.buffer, sp, w * h); } catch (e) {}
      const PC = new Uint8Array(768); for (let i = 0; i < 256; i++) { const c = conv(pal[i]); PC[i * 3] = c[0]; PC[i * 3 + 1] = c[1]; PC[i * 3 + 2] = c[2]; }
      let drawn = 0;
      const now = performance.now() / 1000, wx = Math.floor(now * 6), wy = -Math.floor(now * 6), wt = Math.floor(now * 4);   // ripples run down-left like the source's
      const pu = ((fx >> 1) % PW + PW) % PW, pv = (((fy >> 1) - (O.plainY || 0)) % PH + PH) % PH;
      let KM = null;   // the picture's key pixels before this frame's drawing (the shore looks past them)
      const keyAt = (qx, qy) => { if (!KM) { KM = new Uint8Array(w * h); for (let j = 0, k = off; j < w * h; j++, k += 3) KM[j] = u8[k] === k0 && u8[k + 1] === k1 && u8[k + 2] === k2 ? 1 : 0; } return KM[qy * w + qx] === 1; };
      if (O.water || O.plain) keyAt(0, 0);
      const DE = [];   // drop spots near its rim, finished after the rock is drawn
      const sx0 = Math.max(0, fx >> 3), sx1 = Math.min(W8 - 1, (fx + w - 1) >> 3), sy0 = Math.max(0, fy >> 3), sy1 = Math.min(H8 - 1, (fy + h - 1) >> 3);
      for (let sy = sy0; sy <= sy1; sy++) for (let sx = sx0; sx <= sx1; sx++) {
        const i = sy * W8 + sx, g = GR[i]; if (!g) continue;
        if (g === 0xFFFE) {   // the flood
          const px0 = sx * 8 - fx, py0 = sy * 8 - fy;
          // v267 shore: next to the game's own ground the 8 px steps become a wobbly, rounded waterline. A smooth field
          // (spot centres: water or mountain 1, ground 0, bilinear, plus a slow wobble) cuts each pixel; ground-side pixels
          // take the picture's own shore mirrored across the line, darkened where wet, and a pale foam line rims the water
          let edge = false; for (let dy = -1; dy <= 1 && !edge; dy++) for (let dx = -1; dx <= 1; dx++) { const nx = sx + dx, ny = sy + dy; if (nx >= 0 && ny >= 0 && nx < W8 && ny < H8 && GR[ny * W8 + nx] === 0) { edge = true; break; } }
          const wv = (ax, ay) => (ax < 0 || ay < 0 || ax >= W8 || ay >= H8 || GR[ay * W8 + ax] !== 0) ? 1 : 0;
          for (let y = 0; y < 8; y++) { const py = py0 + y; if (py < 0 || py >= h) continue; const Y = sy * 8 + y;
            for (let x = 0; x < 8; x++) { const px = px0 + x; if (px < 0 || px >= w) continue;
              const kk = off + (py * w + px) * 3; if (u8[kk] !== k0 || u8[kk + 1] !== k1 || u8[kk + 2] !== k2) continue;
              const X = sx * 8 + x, q = ((((Y + wy) & 31) << 5) + ((X + wx) & 31)) * 4;
              let fv = 1;
              if (edge) {
                const u = (X + 0.5) / 8 - 0.5, v = (Y + 0.5) / 8 - 0.5, ix = Math.floor(u), iy = Math.floor(v), tx = u - ix, ty = v - iy;
                fv = (wv(ix, iy) * (1 - tx) + wv(ix + 1, iy) * tx) * (1 - ty) + (wv(ix, iy + 1) * (1 - tx) + wv(ix + 1, iy + 1) * tx) * ty;
                fv += 0.13 * Math.sin(X * 0.41 + Y * 0.17) * Math.sin(Y * 0.33 - X * 0.11) + 0.05 * Math.sin(X * 1.3 + Y * 0.9);
                if (fv < 0.5) {   // shore: the nearest ground pixel's direction, mirrored a little further out
                  let best = 99, bx = 0, by = 0;
                  for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) for (let d = 1; d < Math.min(best, 12); d++) {
                    const qx = px + dx * d, qy = py + dy * d; if (qx < 0 || qy < 0 || qx >= w || qy >= h) break;
                    if (keyAt(qx, qy)) continue;
                    if (d < best) { best = d; bx = dx; by = dy; } break; }
                  if (best < 99) {
                    let qx = px + bx * (2 * best - 1), qy = py + by * (2 * best - 1);
                    if (qx < 0 || qy < 0 || qx >= w || qy >= h) { qx = px + bx * best; qy = py + by * best; }
                    let qk = off + (qy * w + qx) * 3; if (keyAt(qx, qy)) qk = off + ((py + by * best) * w + px + bx * best) * 3;
                    const wet = fv > 0.38 ? 0.72 + (0.5 - fv) * 2.3 : 1;
                    u8[kk] = u8[qk] * wet; u8[kk + 1] = u8[qk + 1] * wet; u8[kk + 2] = u8[qk + 2] * wet;
                    if (tags) tags[py * w + px] = 0; drawn++; continue;
                  }
                  fv = 0.5;
                }
              }
              let R = water[q], G = water[q + 1], B = water[q + 2];
              if (fv < 0.58) { const a = 0.4 * (0.58 - fv) / 0.08; R += (196 - R) * a; G += (206 - G) * a; B += (200 - B) * a; }   // foam at the waterline
              const hh = ((X * 73856093) ^ (Y * 19349663) ^ (wt * 83492791)) >>> 0;   // glints: a few bright pixels, new ones every 1/4 s
              if (hh % 997 === 0) { R = R + 90 > 255 ? 255 : R + 90; G = G + 100 > 255 ? 255 : G + 100; B = B + 100 > 255 ? 255 : B + 100; }
              u8[kk] = R; u8[kk + 1] = G; u8[kk + 2] = B;
              if (tags) tags[py * w + px] = 0; drawn++;
            } }
          continue;
        }
        if (g === 0xFFFF) {   // the drop
          const k = SH[i], px0 = sx * 8 - fx, py0 = sy * 8 - fy;
          for (let y = 0; y < 8; y++) { const py = py0 + y; if (py < 0 || py >= h) continue; const du = k * 8 + y, pr = ((py + pv) % PH) * PW;
            for (let x = 0; x < 8; x++) { const px = px0 + x; if (px < 0 || px >= w) continue;
              const kk = off + (py * w + px) * 3; if (u8[kk] !== k0 || u8[kk + 1] !== k1 || u8[kk + 2] !== k2) continue;
              let q = -1;
              if (k < 255 && du < FH) { const c = (((sx * 8 + x) % FW) + FW) % FW, fq = (du * FW + c) * 4; if (face[fq + 3]) { u8[kk] = face[fq]; u8[kk + 1] = face[fq + 1]; u8[kk + 2] = face[fq + 2]; q = 0; } }
              if (q < 0) { const pq = (pr + (px + pu) % PW) * 4; u8[kk] = plain[pq]; u8[kk + 1] = plain[pq + 1]; u8[kk + 2] = plain[pq + 2]; }
              if (tags) tags[py * w + px] = 0; drawn++;
            } }
          let near = false; for (let dy = -6; dy <= 6 && !near; dy++) for (let dx = -6; dx <= 6; dx++) { if (dx && dy) continue; const nx = sx + dx, ny = sy + dy; if (nx >= 0 && ny >= 0 && nx < W8 && ny < H8 && GR[ny * W8 + nx] !== 0xFFFF) { near = true; break; } }
          if (near) DE.push(sx, sy);
          continue;
        }
        const r = RK[i], f = 1 - O.shade * SH[i] / 15, row = RG[g] * 16, gb = g * 64, rb = r * 256;
        const px0 = sx * 8 - fx, py0 = sy * 8 - fy;
        for (let y = 0; y < 8; y++) { const py = py0 + y; if (py < 0 || py >= h) continue;
          for (let x = 0; x < 8; x++) { const px = px0 + x; if (px < 0 || px >= w) continue;
            const k = off + (py * w + px) * 3; if (u8[k] !== k0 || u8[k + 1] !== k1 || u8[k + 2] !== k2) continue;
            const q = rb + (y * 8 + x) * 4; let R, G, B;
            if (r && rock[q + 3]) { R = rock[q]; G = rock[q + 1]; B = rock[q + 2]; }
            else { const gi = ground[gb + y * 8 + x], p = (gi ? row + gi : 0) * 3; R = PC[p]; G = PC[p + 1]; B = PC[p + 2]; }
            u8[k] = R * f; u8[k + 1] = G * f; u8[k + 2] = B * f;
            if (tags) tags[py * w + px] = 0; drawn++;
          } }
      }
      // v269 the drop's sides: the 8 px steps where rock or ground meets the far valley become a ragged rim (the same
      // rock juts out 0-15 px along a rocky wobble; rim pixels copy the nearest rock or ground shifted by whole spots across
      // the line), and the valley darkens towards the side and lower walls, so the drop reads as a deep cut, not a
      // flat picture pasted beside the rock. The upper edge keeps its earth bank (face).
      const isDrop = (X, Y) => { const ax = X >> 3, ay = Y >> 3; return ax < 0 || ay < 0 || ax >= W8 || ay >= H8 || GR[ay * W8 + ax] === 0xFFFF; };
      for (let e = 0; e < DE.length; e += 2) {
        const sx = DE[e], sy = DE[e + 1], k = SH[sy * W8 + sx], px0 = sx * 8 - fx, py0 = sy * 8 - fy;
        const run = (dx, dy) => { for (let n = 1; n <= 6; n++) if (!isDrop((sx + dx * n) * 8, (sy + dy * n) * 8)) return n; return 99; };
        const kr = run(1, 0), kl = run(-1, 0), kd = run(0, 1), ku = run(0, -1);
        for (let y = 0; y < 8; y++) { const py = py0 + y; if (py < 0 || py >= h) continue; const Y = sy * 8 + y, du = k * 8 + y;
          for (let x = 0; x < 8; x++) { const px = px0 + x; if (px < 0 || px >= w) continue;
            if (!keyAt(px, py)) continue;
            const X = sx * 8 + x;
            if (k < 255 && du < FH) { const c = ((X % FW) + FW) % FW; if (face[(du * FW + c) * 4 + 3]) continue; }   // the earth bank stays
            const kk = off + (py * w + px) * 3;
            // how far the rock juts out here (0-15 px): slow swells plus a rockier small wobble
            const R = 7 + 5 * Math.sin(Y * 0.11 + X * 0.05) * Math.sin(Y * 0.047 - X * 0.03 + 1.3) + 2.5 * Math.sin(Y * 0.37 + X * 0.21) + 1.2 * Math.sin(Y * 1.1 - X * 0.7);
            // nearest rock or ground straight right, left, down or up, from the spot's own counts (cheap on a phone)
            let best = 99, bx = 0, by = 0; const dR = (7 - x) + 8 * kr - 7, dL = x + 8 * kl - 7, dD = (7 - y) + 8 * kd - 7, dU = y + 8 * ku - 7;
            if (dR < best) { best = dR; bx = 1; by = 0; } if (dL < best) { best = dL; bx = -1; by = 0; }
            if (dD < best) { best = dD; bx = 0; by = 1; } if (dU < best) { best = dU; bx = 0; by = -1; }
            if (best >= 44 || by < 0) continue;   // the upper edge has its earth bank
            if (best <= R) {   // ragged rim: the rock (or ground) mirrored past the old straight line
              // shifted whole spots (not mirrored), so the rock's own grain carries on unflipped
              let m = Math.ceil(best / 8) * 8, qx = px + bx * m, qy = py + by * m;
              if (qx < 0 || qy < 0 || qx >= w || qy >= h || isDrop(X + bx * m, Y + by * m)) { m += 8; qx = px + bx * m; qy = py + by * m; }
              if (qx < 0 || qy < 0 || qx >= w || qy >= h || isDrop(X + bx * m, Y + by * m)) { qx = px + bx * best; qy = py + by * best; }
              const qk = off + (qy * w + qx) * 3, lip = best > R - 1.5 ? 0.55 : 1;
              u8[kk] = u8[qk] * lip; u8[kk + 1] = u8[qk + 1] * lip; u8[kk + 2] = u8[qk + 2] * lip;
              continue;
            }
            const dd = best - R; if (dd >= 28) continue;
            let f = 0.38 + 0.62 * Math.pow(dd / 28, 0.7);
            if (dd < 2) f *= 0.6;   // a dark lip right under the rim
            u8[kk] *= f; u8[kk + 1] *= f; u8[kk + 2] *= f;
          } }
      }
      dbg.drawn = drawn;
      // steam from the drowned pits: soft puffs rise ~80 px, drift with the wind, swell and fade; drawn over everything
      if (O.vents) for (let v = 0; v < O.vents.length; v++) {
        const vx = O.vents[v][0] - fx, vy = O.vents[v][1] - fy;
        if (vx < -60 || vx > w + 60 || vy < -20 || vy > h + 100) continue;
        for (let n = 0; n < 12; n++) {
          const ph = (now / 6 + n / 12 + v * 0.37) % 1, s = Math.sin(v * 12.9898 + n * 78.233) * 43758.5453, rj = s - Math.floor(s);
          const cx = vx + (rj - 0.5) * 10 + ph * 16 + Math.sin(now * 0.8 + n + v) * 3 * ph, cy = vy - ph * 90, rad = 6 + ph * 18;
          const a0 = 0.75 * Math.sin(Math.PI * Math.pow(ph, 0.75)) * (1 - ph * 0.5) * (0.7 + 0.3 * rj);
          const xa = Math.max(0, Math.floor(cx - rad)), xb = Math.min(w - 1, Math.ceil(cx + rad)), ya = Math.max(0, Math.floor(cy - rad)), yb = Math.min(h - 1, Math.ceil(cy + rad));
          for (let py = ya; py <= yb; py++) for (let px = xa; px <= xb; px++) {
            const dd = ((px - cx) * (px - cx) + (py - cy) * (py - cy)) / (rad * rad); if (dd >= 1) continue;
            const a = a0 * Math.sqrt(1 - dd), kk = off + (py * w + px) * 3;
            u8[kk] += (222 - u8[kk]) * a; u8[kk + 1] += (224 - u8[kk + 1]) * a; u8[kk + 2] += (220 - u8[kk + 2]) * a;
          }
        }
      }
    };

    // v266 Isengard's sound (plan step 8, "life"): wind over the plain, water lapping and bubbling in the drowned pits,
    // steam hissing from the vents and, now and then, a warg pack howling in the distance. Made in WebAudio on the game's
    // own sound player (window.__preAudio, so it starts from the same Play tap on phones); it follows the camera
    // (window.__mtnView, set each frame while Isengard is shown) and fades out within half a second of leaving it.
    (() => {
      let A = null, out = null, wind = null, water = null, steam = null, nextHowl = 0, nextBub = 0;
      const amb = { wind: 0, water: 0, steam: 0, howls: 0 }; window.__ambDbg = amb;
      const noise = (ctx, brown) => { const n = ctx.sampleRate * 4, b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); let l = 0;
        for (let i = 0; i < n; i++) { const r = Math.random() * 2 - 1; if (brown) { l = (l + 0.02 * r) / 1.02; d[i] = l * 3.5; } else d[i] = r; }
        const s = ctx.createBufferSource(); s.buffer = b; s.loop = true; return s; };
      const chain = (ctx, src, nodes, g0) => { let n = src; for (const f of nodes) { n.connect(f); n = f; } const g = ctx.createGain(); g.gain.value = g0; n.connect(g); g.connect(out); src.start(); return g; };
      const filt = (ctx, type, f, q) => { const b = ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; if (q) b.Q.value = q; return b; };
      const setup = () => {
        const ctx = window.__preAudio; if (!ctx || ctx.state !== "running") return false;
        A = ctx; out = ctx.createGain(); out.gain.value = 0; out.connect(ctx.destination);
        const wl = filt(ctx, "lowpass", 520, 0.7); wind = { g: chain(ctx, noise(ctx, true), [wl], 0), f: wl, gust: 0.5 };
        const wb = filt(ctx, "bandpass", 700, 0.9); water = { g: chain(ctx, noise(ctx, false), [wb, filt(ctx, "lowpass", 1600)], 0), f: wb };
        steam = { g: chain(ctx, noise(ctx, false), [filt(ctx, "highpass", 2600), filt(ctx, "bandpass", 5200, 0.6)], 0) };
        return true;
      };
      // a bubble: a short sine whose pitch rises as it closes (real bubbles ring upward), quiet and soft at both ends
      const bubble = (t, vol) => { const o = A.createOscillator(), g = A.createGain(), f0 = 380 + Math.random() * 700;
        o.type = "sine"; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f0 * (1.6 + Math.random() * 0.6), t + 0.06);
        g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);
        o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.1); };
      // a far howl: a breathy saw through two vowel formants, rising, held with a slow wobble, then sinking away; a
      // second, quieter voice answers a moment later; a lowpass and a little echo put it far off
      const howl = (t, vol) => {
        const lp = filt(A, "lowpass", 1500), dl = A.createDelay(1), fb = A.createGain(); dl.delayTime.value = 0.23; fb.gain.value = 0.28;
        lp.connect(out); lp.connect(dl); dl.connect(fb); fb.connect(dl); dl.connect(out);
        const voice = (t0, f, v, len) => { const o = A.createOscillator(), vib = A.createOscillator(), vg = A.createGain(), g = A.createGain();
          o.type = "sawtooth"; vib.frequency.value = 4.6; vg.gain.value = f * 0.012; vib.connect(vg); vg.connect(o.frequency);
          o.frequency.setValueAtTime(f * 0.62, t0); o.frequency.exponentialRampToValueAtTime(f, t0 + 0.55); o.frequency.setValueAtTime(f, t0 + 0.55 + len);
          o.frequency.exponentialRampToValueAtTime(f * 0.7, t0 + 1.4 + len);
          g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(v, t0 + 0.35); g.gain.setValueAtTime(v, t0 + 0.55 + len); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.5 + len);
          const f1 = filt(A, "bandpass", 760, 4), f2 = filt(A, "bandpass", 1150, 5), d = filt(A, "lowpass", 900), dg = A.createGain(), m = A.createGain(); dg.gain.value = 0.3;
          o.connect(f1); o.connect(f2); o.connect(d); d.connect(dg); f1.connect(m); f2.connect(m); dg.connect(m); m.connect(g); g.connect(lp);
          o.start(t0); vib.start(t0); o.stop(t0 + 1.6 + len); vib.stop(t0 + 1.6 + len); };
        voice(t, 520 + Math.random() * 60, vol, 0.9 + Math.random() * 0.5);
        if (Math.random() < 0.7) voice(t + 0.8 + Math.random() * 0.9, 600 + Math.random() * 80, vol * 0.6, 0.6 + Math.random() * 0.4);
        amb.howls++; };
      const near = (x, y) => {   // water and vent amounts round the listener, 0..1, nearer counts more
        let wa = 0, st = 0; if (GR) { for (let dy = -22; dy <= 22; dy += 2) for (let dx = -26; dx <= 26; dx += 2) { const sx = (x >> 3) + dx, sy = (y >> 3) + dy;
          if (sx < 0 || sy < 0 || sx >= W8 || sy >= H8 || GR[sy * W8 + sx] !== 0xFFFE) continue; wa += 1 / (1 + (dx * dx + dy * dy) / 60); } }
        if (O.vents) for (const v of O.vents) { const d2 = (v[0] - x) ** 2 + (v[1] - y) ** 2; if (d2 < 260 * 260) st += 1 / (1 + d2 / (70 * 70)); }
        return [Math.min(1, wa / 28), Math.min(1, st / 1.6)]; };
      setInterval(() => { try {
        if (!A && !setup()) return;
        const v = window.__mtnView, on = !!(v && performance.now() - v.t < 400) && A.state === "running", t = A.currentTime;
        out.gain.setTargetAtTime(on ? 1 : 0, t, on ? 0.6 : 0.12);
        if (!on) return;
        const [wa, st] = near(v.x, v.y);
        // gusts: a slow random walk; the plain is windier than the pits' hollows
        wind.gust = Math.max(0.15, Math.min(1, wind.gust + (Math.random() - 0.5) * 0.18));
        const wv = 0.08 * (0.35 + 0.65 * wind.gust) * (1 - 0.5 * wa);
        wind.g.gain.setTargetAtTime(wv, t, 0.5); wind.f.frequency.setTargetAtTime(320 + 520 * wind.gust, t, 0.6);
        water.g.gain.setTargetAtTime(0.09 * wa * (0.6 + 0.4 * Math.random()), t, 0.15); water.f.frequency.setTargetAtTime(520 + Math.random() * 420, t, 0.2);
        steam.g.gain.setTargetAtTime(0.07 * st * (0.75 + 0.25 * Math.random()), t, 0.12);
        if (wa > 0.08 && t > nextBub) { bubble(t + Math.random() * 0.1, 0.04 + 0.06 * wa); nextBub = t + 0.12 + Math.random() * (1.4 - wa); }
        if (O.wolves && t > nextHowl) {   // a pack 300-1100 px away: out of sight but near enough to hear
          let best = 1e9; for (const w of O.wolves) { const d = Math.hypot(w[0] - v.x, w[1] - v.y); if (d > 300 && d < best) best = d; }
          if (best < 1100 && Math.random() < 0.5) howl(t + 0.05, 0.12 * (1 - best / 1300));
          nextHowl = t + 25 + Math.random() * 25;
        }
        amb.wind = +wv.toFixed(3); amb.water = +wa.toFixed(2); amb.steam = +st.toFixed(2);
      } catch (e) { amb.err = String(e); } }, 250);
    })();
  })();
