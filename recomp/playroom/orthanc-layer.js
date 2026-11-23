  // v247 Orthanc's four horns (tools/region/orthanc): drawn from the tower's own tiles as a layer over the game's picture,
  // so the hero walks behind them; the tower casts its shadow east, and the horns lean a little away from the middle of
  // the screen for height. The layer is placed to the pixel by matching the region's ground against the picture (the
  // camera in memory runs ahead of the in-between pictures). Works in 1-player, P2 and online (all draw through WideHost).
  (() => {
    const O = __ORTHANC__;
    let top = null, shadow = null, last = [0, 0], miss = 0;
    const load = (b64, cb) => { try { const im = new Image(); im.onload = () => { try { const c = document.createElement("canvas"); c.width = im.width; c.height = im.height; const x = c.getContext("2d"); x.drawImage(im, 0, 0); cb(x.getImageData(0, 0, im.width, im.height).data); } catch (e) {} }; im.src = "data:image/png;base64," + b64; } catch (e) {} };
    load(O.top, (d) => {   // opaque runs per row
      const rows = [], rgb = new Uint8Array(O.w * O.h * 3); let n = 0;
      for (let y = 0; y < O.h; y++) { const r = []; let x = 0;
        while (x < O.w) { while (x < O.w && d[(y * O.w + x) * 4 + 3] < 128) x++; if (x >= O.w) break; const a = x, at = n;
          while (x < O.w && d[(y * O.w + x) * 4 + 3] >= 128) { const k = (y * O.w + x) * 4; rgb[n * 3] = d[k]; rgb[n * 3 + 1] = d[k + 1]; rgb[n * 3 + 2] = d[k + 2]; n++; x++; }
          r.push(a, x, at); }
        rows.push(r); }
      top = { rows, rgb };
    });
    load(O.shadow, (d) => { const a = new Uint8Array(O.sw * O.sh); for (let i = 0; i < a.length; i++) a[i] = d[i * 4]; shadow = a; });
    const S = O.samples;
    // mean colour difference of the samples at frame offset (fx, fy) = level px of the picture's (0, 0)
    let V = [];   // the samples near the picture this time (at most 400, spread out)
    const pick = (ex, ey, w, h) => { V = []; for (let i = 0; i < S.length; i++) { const p = S[i]; if (p[0] >= ex - 12 && p[1] >= ey - 12 && p[0] < ex + w + 12 && p[1] < ey + h + 12) V.push(p); }
      if (V.length > 400) { const k = V.length / 400, W = []; for (let i = 0; i < 400; i++) W.push(V[Math.floor(i * k)]); V = W; } };
    const score = (u8, off, w, h, fx, fy) => { let s = 0, n = 0;
      for (let i = 0; i < V.length; i++) { const p = V[i], x = p[0] - fx, y = p[1] - fy; if (x < 0 || y < 0 || x >= w || y >= h) continue;
        const k = off + (y * w + x) * 3; s += Math.abs(u8[k] - p[2]) + Math.abs(u8[k + 1] - p[3]) + Math.abs(u8[k + 2] - p[4]); n++; }
      return n >= 24 ? s / n : -1; };
    let dbg = {}; window.__orthancDbg = { last: () => last, miss: () => miss, info: () => Object.assign({ top: !!top, shadow: !!shadow }, dbg) };
    window.__orthanc = (u8, off, w, h) => {
      const M = window.__wideM; if (!M || !top || !M._rotk_iwram || w < 240 || h < 160) return;
      const iw = M._rotk_iwram(), H8 = M.HEAPU8, r32 = (a) => (H8[iw + a] | H8[iw + a + 1] << 8 | H8[iw + a + 2] << 16 | H8[iw + a + 3] << 24);
      if (H8[iw + 0x4174] !== O.level || r32(0x41B0) !== 1) return;
      const ex = r32(0x5880) - ((w - 240) >> 1), ey = r32(0x5884) - ((h - 160) >> 1);   // camera: level px of the picture's (0, 0)
      // is the tower anywhere near the picture?
      if (ex + w < Math.min(O.x, O.sx) - 64 || ex > Math.max(O.x + O.w, O.sx + O.sw) + 64 || ey + h < O.y - 64 || ey > Math.max(O.y + O.h, O.sy + O.sh) + 400) return;
      // place it: the last offset from the camera first, then a search around it
      pick(ex, ey, w, h);
      let best = score(u8, off, w, h, ex + last[0], ey + last[1]), bx = last[0], by = last[1];
      if (best < 0) { bx = by = 0; }
      else if (best > 45) {
        for (let dy = -12; dy <= 12; dy++) for (let dx = -12; dx <= 12; dx++) {
          const s = score(u8, off, w, h, ex + dx, ey + dy); if (s >= 0 && s < best) { best = s; bx = dx; by = dy; } }
        if (best > 70) { miss++; bx = last[0]; by = last[1]; } else last = [bx, by];
      }
      const fx = ex + bx, fy = ey + by;
      // HD tiles (skin) are looked up per pixel from the engine's tile tags: pixels we draw get no tag, so they stay ours
      let tags = null; try { const sp = M._rotk_skin_slot ? M._rotk_skin_slot(window.GbrHost.front) : 0; if (sp) tags = new Uint32Array(M.HEAPU8.buffer, sp, w * h); } catch (e) {} dbg = { best, bx, by, n: V.length, ex, ey, w, h };
      // shadow on the ground
      if (shadow) {
        const x0 = Math.max(0, O.sx - fx), x1 = Math.min(w, O.sx + O.sw - fx), y0 = Math.max(0, O.sy - fy), y1 = Math.min(h, O.sy + O.sh - fy);
        for (let y = y0; y < y1; y++) { const sr = (y + fy - O.sy) * O.sw + fx - O.sx; let k = off + (y * w + x0) * 3;
          const tr = y * w;
          for (let x = x0; x < x1; x++, k += 3) { const a = shadow[sr + x]; if (a) { const m = 255 - a; u8[k] = u8[k] * m >> 8; u8[k + 1] = u8[k + 1] * m >> 8; u8[k + 2] = u8[k + 2] * m >> 8; if (tags) tags[tr + x] = 0; } } }
      }
      // the horns: the bottom row stays on the tower in the map; higher rows lean away from the middle of the screen
      const bx0 = O.x - fx, by0 = O.y + O.h - fy;                 // picture spot of the layer's bottom-left
      const lx = (bx0 + O.w / 2 - w / 2) / (w / 2), ly = (by0 - h / 2) / (h / 2);   // -1..1 off the middle
      const kx = 0.022 * Math.max(-1.5, Math.min(1.5, lx)), ky = 1 - 0.03 * Math.max(-1.5, Math.min(1.5, ly));
      const tall = Math.round(O.h * ky);
      for (let t = 0; t < tall; t++) {                            // t = height above the bottom row, in picture px
        const y = by0 - 1 - t; if (y < 0) break; if (y >= h) continue;
        const sr = O.h - 1 - Math.min(O.h - 1, Math.floor(t / ky)), row = top.rows[sr], sx = bx0 + Math.round(kx * t);
        for (let i = 0; i < row.length; i += 3) {
          let a = row[i] + sx, b = row[i + 1] + sx, at = row[i + 2];
          if (a < 0) { at -= a; a = 0; } if (b > w) b = w; if (a >= b) continue;
          let k = off + (y * w + a) * 3, q = at * 3;
          for (let x = a; x < b; x++, k += 3, q += 3) { u8[k] = top.rgb[q]; u8[k + 1] = top.rgb[q + 1]; u8[k + 2] = top.rgb[q + 2]; }
          if (tags) tags.fill(0, y * w + a, y * w + b);
        }
      }
    };
  })();
