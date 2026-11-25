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
      const sx0 = Math.max(0, fx >> 3), sx1 = Math.min(W8 - 1, (fx + w - 1) >> 3), sy0 = Math.max(0, fy >> 3), sy1 = Math.min(H8 - 1, (fy + h - 1) >> 3);
      for (let sy = sy0; sy <= sy1; sy++) for (let sx = sx0; sx <= sx1; sx++) {
        const i = sy * W8 + sx, g = GR[i]; if (!g) continue;
        if (g === 0xFFFE) {   // the flood
          const px0 = sx * 8 - fx, py0 = sy * 8 - fy;
          for (let y = 0; y < 8; y++) { const py = py0 + y; if (py < 0 || py >= h) continue; const Y = sy * 8 + y;
            for (let x = 0; x < 8; x++) { const px = px0 + x; if (px < 0 || px >= w) continue;
              const kk = off + (py * w + px) * 3; if (u8[kk] !== k0 || u8[kk + 1] !== k1 || u8[kk + 2] !== k2) continue;
              const X = sx * 8 + x, q = ((((Y + wy) & 31) << 5) + ((X + wx) & 31)) * 4;
              let R = water[q], G = water[q + 1], B = water[q + 2];
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
  })();
