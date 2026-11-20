// v224 "Modern classic" (Jordan, 2026-11-20: "Can we upgrade the stat menu skills menu and inventory menus to all feel
// more modern as well as shrine menus and forge ... Should feel like a modern classic" / "Let's increase the size of the
// hud and do the same modern classic"). The look of the new title and pause menus (dark stone, gold edges, a painted
// dusk sky, parchment) carried over to:
//   - Stats (state 14) and Skills (state 15), drawn by the page from the game's own numbers while the game keeps running
//     the screens (its cursor, Left / Right to place points, A to learn a skill level, L / R to turn pages, B to close).
//       Stats: hero struct P = 0x03003C00 + 0x1AC * [0x03003F59], as the game's own page (0x08027D80..0x08028080):
//         Experience = sum of the level table 0x080628D0 below the level + P+0x178, Next Level = table[level] - P+0x178,
//         Hit Points P+0x17C / P+0xD0, Spirit P+0x17E / P+0xD2, Damage = (f1 >> 1) + f2 .. f1 + f2 (0x08027904 / 0x08027984),
//         Melee Armor P+0xBE, Missile Armor P+0xC0, To Hit P+0xC8 %, Dodge P+0xFC %, Shield Block P+0x100 %,
//         attributes P+0xC6 + 2 * i (Strength, Accuracy, Health, Defense, Courage), compared with the page's pending
//         values 0x03001CE8 + 12 * player + 10 - 2 * i, points P+0x19D, cursor 0x030041B8.
//       Skills: sub 0x030041C0 = 2 passive (3 x 3), 1 active (3 / 2 / 1), cursor 0x030041B8; levels P+0x161 + k (passive)
//         and P+0x16A + k (active), skill points P+0x19E, A / B / R slots P+0x191..0x193. The focused skill's words are
//         the game's own: the text it decoded (pointer at 0x03002160) with its @1 / @2 values (0x03001B90 + 0x40 * n).
//         Other skills' names come from the game's text bank (passive ids at 0x03006A10, text 482 + id; active text
//         517 + 6 * hero + k). Icons and the hero picture are cut from the game's own picture of the page
//         (window.__gbaFrame), turned gold and smoothed.
//   - the HD Backpack, Forge and Shrine: the same backdrop, gold-framed panels and boxes, gold-ringed buttons.
//   - a bigger HUD in the same look: Hit Points and Spirit bars with numbers, experience, level, Ent Water and
//     Kingsfoil, and the game's skill orb, over the game's own small HUD.
// Works the same in 1-player, P2 and online games (it reads the local game, and presses travel with the buttons).
(() => {
  const ST = 0x41B0, SUB = 0x41C0, CUR = 0x41B8;
  const HERO = ["Frodo", "Legolas", "Aragorn", "Gandalf", "Éowyn", "Gimli", "Sam", "Sméagol"];
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const view = () => {
    const M = window.__wideM; if (!M || !M.HEAPU8 || !M._rotk_iwram) return null;
    if (M._rotk_link_iwram && M._rotk_link_on && M._rotk_link_on() && window.__mp && window.__mp.online && !window.__mp.sync) return null;
    const onl = !!(window.__mp && window.__mp.online), me = onl ? window.__mp.me & 1 : 0;
    const iw = onl && M._rotk_link_iwram ? M._rotk_link_iwram(me) : M._rotk_iwram();
    const ew = onl && M._rotk_link_ewram ? M._rotk_link_ewram(me) : M._rotk_ewram ? M._rotk_ewram() : 0;
    return iw ? { H: M.HEAPU8, iw, ew } : null;
  };
  const gi = (id, v) => { window.__padOwn = (window.__padOwn || 0) + 1; try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} window.__padOwn--; };
  const press = (id, ms = 90) => { const d = window.__mp && window.__mp.sync ? 50 : 0; setTimeout(() => { gi(id, 1); setTimeout(() => gi(id, 0), ms); }, d); };
  const key = (k) => { if (k === "L" && window.__lBlip) window.__lBlip(); else press({ L: 10, R: 11, A: 8, B: 0, U: 4, D: 5, l: 6, r: 7 }[k]); };
  const u16 = (H, o) => H[o] | H[o + 1] << 8, s16 = (H, o) => (H[o] | H[o + 1] << 8) << 16 >> 16;
  const u32 = (H, o) => (H[o] | H[o + 1] << 8 | H[o + 2] << 16 | H[o + 3] << 24) >>> 0;
  const cstr = (H, o, n) => { let s = ""; for (let i = 0; i < n; i++) { const c = H[o + i]; if (!c) break; s += c >= 32 && c < 127 ? String.fromCharCode(c) : c === 10 ? " " : ""; } return s; };
  // a GBA address (0x02xxxxxx EWRAM / 0x03xxxxxx IWRAM) in the local game
  const gba = (v, a) => (a >>> 24) === 2 ? v.ew + (a & 0x3ffff) : (a >>> 24) === 3 ? v.iw + (a & 0x7fff) : -1;

  // ---- the game's text bank (Huffman, tools/text.py): names of the skills that aren't focused ----
  const textCache = new Map();
  const text = (idx) => {
    const R = window.__romFull; if (!R) return "";
    if (textCache.has(idx)) return textCache.get(idx);
    let out = "";
    try {
      const bank = u32(R, 0x289A10) - 0x08000000, tree = bank + 4, table = tree + u32(R, bank);
      let p = bank + u32(R, table + 4 * idx), node = 0x100, bit = 0, byte = R[p++];
      while (out.length < 600) {
        while (node > 0xFF) { const e = tree + (node - 0x100) * 4; node = u16(R, (byte >> bit) & 1 ? e + 2 : e); if (++bit === 8) { bit = 0; byte = R[p++]; } }
        if (!node) break;
        out += String.fromCharCode(node); node = 0x100;
      }
    } catch (e) { out = ""; }
    textCache.set(idx, out);
    return out;
  };
  const skillName = (s) => s.split(/ \((?:Level|level)/)[0].trim();

  // ---- the game's own picture: cut a box out of it ----
  const frame = () => { try { const f = window.__gbaFrame && window.__gbaFrame(); return f && f.w >= 240 && f.h >= 160 ? f : null; } catch (e) { return null; } };
  const crop = (f, x, y, w, h) => {
    const im = new ImageData(w, h);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const sx = x + i, sy = y + j; if (sx < 0 || sy < 0 || sx >= f.w || sy >= f.h) continue;
      const o = f.off + (sy * f.w + sx) * 3, d = (j * w + i) * 4;
      im.data[d] = f.u8[o]; im.data[d + 1] = f.u8[o + 1]; im.data[d + 2] = f.u8[o + 2]; im.data[d + 3] = 255;
    }
    return im;
  };
  // EPX / Scale2x: pixel art doubled with its diagonals kept, before the browser smooths it
  const epx = (im) => {
    const w = im.width, h = im.height, s = new Uint32Array(im.data.buffer.slice(0)), o = new ImageData(w * 2, h * 2), d = new Uint32Array(o.data.buffer);
    const at = (x, y) => s[Math.min(h - 1, Math.max(0, y)) * w + Math.min(w - 1, Math.max(0, x))];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const P = at(x, y), A = at(x, y - 1), B = at(x + 1, y), C = at(x - 1, y), D = at(x, y + 1);
      const i = y * 4 * w + x * 2;
      d[i] = C === A && C !== D && A !== B ? A : P; d[i + 1] = A === B && A !== C && B !== D ? B : P;
      d[i + 2 * w] = D === C && D !== B && C !== A ? C : P; d[i + 2 * w + 1] = B === D && B !== A && D !== C ? D : P;
    }
    return o;
  };
  const toURL = (im, W, H) => {
    const a = document.createElement("canvas"); a.width = im.width; a.height = im.height; a.getContext("2d").putImageData(im, 0, 0);
    const b = document.createElement("canvas"); b.width = W; b.height = H; const x = b.getContext("2d"); x.imageSmoothingQuality = "high"; x.drawImage(a, 0, 0, W, H);
    return b.toDataURL();
  };
  // a skill icon (32 x 24, an oval medallion) as a gold relief: the picture's light and shade on a gold ramp
  const GOLD = [[22, 12, 4], [92, 58, 20], [176, 124, 52], [236, 196, 112], [255, 244, 206]];
  const ramp = (t) => { t = Math.max(0, Math.min(1, t)) * 4; const i = Math.min(3, t | 0), f = t - i, a = GOLD[i], b = GOLD[i + 1]; return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]; };
  const medal = (f, x, y) => {
    const im = crop(f, x, y, 32, 24), dd = im.data;
    for (let j = 0; j < 24; j++) for (let i = 0; i < 32; i++) {
      const d = (j * 32 + i) * 4, nx = (i - 15.5) / 14.6, ny = (j - 11.5) / 11.2;
      if (nx * nx + ny * ny > 1) { dd[d + 3] = 0; continue; }
      const L = (0.3 * dd[d] + 0.59 * dd[d + 1] + 0.11 * dd[d + 2]) / 255, c = ramp(Math.pow(L, 0.8) * 1.15);
      dd[d] = c[0]; dd[d + 1] = c[1]; dd[d + 2] = c[2];
    }
    return toURL(epx(epx(im)), 128, 128);
  };

  // ---- the painted backdrop (hd-menus.js), darkened, one picture per size ----
  const bgCache = {};
  const backdrop = (w, h) => {
    const W = Math.max(64, Math.round(w / 16) * 16), H = Math.max(64, Math.round(h / 16) * 16), k = W + "x" + H;
    if (bgCache[k] !== undefined) return bgCache[k];
    let url = "";
    try {
      if (window.__hdPaint) {
        const c = document.createElement("canvas"), sc = Math.min(1.5, window.devicePixelRatio || 1);
        c.width = Math.round(W * sc); c.height = Math.round(H * sc); window.__hdPaint(c); url = c.toDataURL("image/jpeg", 0.86);
      }
    } catch (e) { url = ""; }
    return (bgCache[k] = url);
  };

  // ---- shared look ----
  const CSS =
    '.hdx{--gold:#e9c46f;--gold2:#c99a46;--ink:#f3ead6;--parch:radial-gradient(ellipse at 35% 35%,#fbf1d4,#ecd9a8 62%,#d2b57a)}' +
    // the Backpack / Forge / Shrine: same backdrop, gold-framed panels, boxes and buttons. Plain "body #id .x" rules sit
    // below the pages' own two-class rules (green / red / gold / cursor boxes keep their look).
    'body #hdBp,body #hdSh{background:linear-gradient(rgba(10,8,6,.34),rgba(6,5,4,.55)),var(--hdbg,none) center/cover no-repeat,#0b0907}' +
    'body #hdBp .pg,body #hdSh .pg{border:1.5px solid #c99a46;border-radius:6px;background:linear-gradient(180deg,rgba(30,26,22,.84),rgba(12,10,8,.9));' +
      'box-shadow:0 0 0 1px #2a1d0c,0 0 0 4px rgba(12,10,8,.7),0 0 0 5px rgba(201,154,70,.5),inset 0 0 calc(var(--fs)*2.2) rgba(0,0,0,.65),0 10px 26px rgba(0,0,0,.6)}' +
    'body #hdBp .pg::after,body #hdSh .pg::after{content:"";position:absolute;left:50%;top:0;width:calc(var(--fs)*.62);height:calc(var(--fs)*.62);background:linear-gradient(135deg,#fff1c0,#c88d2e);transform:translate(-50%,-50%) rotate(45deg);box-shadow:0 0 0 1px #3a2a12,0 0 7px rgba(255,200,90,.8);pointer-events:none}' +
    'body #hdBp .hdr,body #hdSh .hdr{font-family:var(--display,Georgia,serif);color:#e9c46f;opacity:1;letter-spacing:.2em;padding:0 calc(var(--fs)*1.2);background:linear-gradient(90deg,#c99a46,transparent) left center/calc(var(--fs)*.9) 1px no-repeat,linear-gradient(270deg,#c99a46,transparent) right center/calc(var(--fs)*.9) 1px no-repeat;text-shadow:0 1px 2px #000}' +
    'body #hdBp .cell,body #hdSh .cell{background:radial-gradient(ellipse at 50% 30%,#3d3326,#1b1610 72%);border:1.5px solid #8a6a30;border-radius:calc(var(--c)*.1);box-shadow:inset 0 0 0 1px rgba(0,0,0,.65),inset 0 3px 9px rgba(0,0,0,.6),0 1px 0 rgba(255,220,150,.1)}' +
    'body #hdBp .cell.cur,body #hdSh .cell.cur{border-color:#ffe08a;box-shadow:0 0 0 2px #f6c45a,0 0 calc(var(--c)*.35) rgba(255,190,80,.9),inset 0 0 calc(var(--c)*.25) rgba(255,200,110,.25)}' +
    'body #hdBp .bar b,body #hdSh .bar b{white-space:nowrap;padding:calc(var(--fs)*.42) calc(var(--fs)*.75);border:1.5px solid #c99a46;background:linear-gradient(#1f1c20,#0d0c10);color:#f3d27a;box-shadow:0 0 0 1px #000,0 3px 8px rgba(0,0,0,.6);text-shadow:0 1px 2px #000}' +
    'body #hdBp .acts b,body #hdSh .acts b{border:1.5px solid #8a6a30;background:linear-gradient(#1f1c20,#0d0c10);color:#efe4cc;font-family:var(--display,Georgia,serif);letter-spacing:.04em}' +
    'body #hdBp .acts b.sel,body #hdSh .acts b.sel,body #hdSh .bar b.cur{border-color:#ffe08a;background:linear-gradient(#fff0b8,#d8a240 50%,#f2cf78);color:#2b1d10;box-shadow:0 0 calc(var(--fs)*.6) rgba(255,190,80,.8)}' +
    'body #hdBp .nm,body #hdSh .nm{text-shadow:0 1px 3px #000}' +
    'body #hdBp.tl,body #hdSh.tl{flex-direction:column;gap:calc(var(--fs)*1.1);padding-top:calc(var(--fs)*1.2)}body #hdBp.tl .lp,body #hdSh.tl .lp{flex:1 1 auto;min-height:0}body #hdBp.tl .rp,body #hdSh.tl .rp{flex:0 0 auto;gap:calc(var(--fs)*.5)}' +
    'body #hdBp .big,body #hdSh .big{border-radius:50%;background:radial-gradient(circle,rgba(255,214,140,.22),rgba(0,0,0,0) 68%)}' +
    // the HD Stats / Skills pages
    '#hdPg{position:fixed;z-index:23;box-sizing:border-box;overflow:hidden;color:#f3ead6;font:600 var(--fs,14px)/1.25 var(--ui,system-ui,sans-serif);user-select:none;-webkit-user-select:none;touch-action:none;' +
      'background:linear-gradient(rgba(10,8,6,.34),rgba(6,5,4,.55)),var(--hdbg,none) center/cover no-repeat,#0b0907;display:flex;flex-direction:column;padding:calc(var(--fs)*.5) calc(var(--fs)*1) calc(var(--fs)*.55);gap:calc(var(--fs)*.45)}' +
    '#hdPg[hidden]{display:none}' +
    '#hdPg .top{display:flex;align-items:center;justify-content:space-between;gap:calc(var(--fs)*.6);flex:0 0 auto}' +
    '#hdPg .ttl{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center}' +
    '#hdPg .ttl b{font:700 calc(var(--fs)*1.65)/1.05 var(--display,Georgia,serif);letter-spacing:.04em;background:linear-gradient(#fff3c9,#e7b552 55%,#a8742a);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 3px rgba(0,0,0,.85));white-space:nowrap}' +
    '#hdPg .ttl i{font:600 calc(var(--fs)*.78)/1.2 var(--display,Georgia,serif);font-style:normal;letter-spacing:.22em;text-transform:uppercase;color:#d9c08a;opacity:.9}' +
    '#hdPg .orn{width:70%;height:calc(var(--fs)*.55);background:linear-gradient(90deg,transparent,#d9a94c 20%,#f6dc93 50%,#d9a94c 80%,transparent) center/100% 1.5px no-repeat;position:relative}' +
    '#hdPg .orn::after{content:"";position:absolute;left:50%;top:50%;width:calc(var(--fs)*.42);height:calc(var(--fs)*.42);background:linear-gradient(135deg,#fff1c0,#c88d2e);transform:translate(-50%,-50%) rotate(45deg);box-shadow:0 0 6px rgba(255,200,90,.8)}' +
    '#hdPg .pill{display:inline-flex;align-items:center;gap:calc(var(--fs)*.4);padding:calc(var(--fs)*.32) calc(var(--fs)*.85);border:1.5px solid #c99a46;border-radius:999px;background:linear-gradient(#1f1c20,#0d0c10);color:#f3d27a;cursor:pointer;' +
      'font:700 calc(var(--fs)*.82)/1 var(--display,Georgia,serif);letter-spacing:.05em;white-space:nowrap;box-shadow:0 0 0 1px #000,0 3px 8px rgba(0,0,0,.6);text-shadow:0 1px 2px #000}' +
    '#hdPg .pill.go{border-color:#ffe08a;background:linear-gradient(#fff0b8,#d8a240 50%,#f2cf78);color:#2b1d10;text-shadow:none;box-shadow:0 0 calc(var(--fs)*.7) rgba(255,190,80,.75)}' +
    '#hdPg .pill.off{opacity:.45}' +
    '#hdPg .pill u{text-decoration:none;display:grid;place-items:center;width:calc(var(--fs)*1.15);height:calc(var(--fs)*1.15);border-radius:50%;background:radial-gradient(#fff,#c9c3b6);color:#222;font:700 calc(var(--fs)*.62)/1 var(--ui,system-ui,sans-serif)}' +
    '#hdPg .cp{display:inline-flex;align-items:center;gap:.4em;padding:calc(var(--fs)*.2) calc(var(--fs)*.7);border-radius:999px;border:1px solid rgba(233,196,111,.6);background:rgba(10,8,6,.7);color:#f6e2a8;font:700 calc(var(--fs)*.8)/1.1 var(--ui,system-ui,sans-serif);white-space:nowrap}' +
    '#hdPg .cp em{font-style:normal;color:#ffe08a;font-size:1.2em}#hdPg .cp.hot{border-color:#ffe08a;box-shadow:0 0 calc(var(--fs)*.6) rgba(255,190,80,.6)}' +
    '#hdPg .main{flex:1 1 auto;min-height:0;display:flex;gap:calc(var(--fs)*.7);margin-top:calc(var(--fs)*.55)}' +
    '#hdPg .pc{position:relative;display:block;gap:0;width:auto;min-width:0;min-height:0;box-sizing:border-box;border:1.5px solid #c99a46;border-radius:6px;padding:calc(var(--fs)*.75) calc(var(--fs)*.8) calc(var(--fs)*.6);' +
      'background:linear-gradient(180deg,rgba(30,26,22,.84),rgba(12,10,8,.9));box-shadow:0 0 0 1px #2a1d0c,0 0 0 4px rgba(12,10,8,.7),0 0 0 5px rgba(201,154,70,.45),inset 0 0 calc(var(--fs)*2) rgba(0,0,0,.6),0 10px 24px rgba(0,0,0,.55)}' +
    '#hdPg .pc>h4{position:absolute;left:50%;top:0;transform:translate(-50%,-55%);margin:0;padding:calc(var(--fs)*.12) calc(var(--fs)*.8);white-space:nowrap;border:1px solid #c99a46;border-radius:3px;background:linear-gradient(90deg,#101a33,#1d2c52 50%,#101a33);' +
      'font:700 calc(var(--fs)*.7)/1.2 var(--display,Georgia,serif);letter-spacing:.2em;text-transform:uppercase;color:#f0d38a;box-shadow:0 2px 6px rgba(0,0,0,.6)}' +
    '#hdPg .parch{color:#2b1d10;background:var(--parch);border:2px solid #b8893a;border-radius:4px;box-shadow:0 0 0 1px #4a3415,inset 0 0 calc(var(--fs)*1.3) rgba(120,80,30,.45),0 4px 12px rgba(0,0,0,.6)}' +
    '#hdPg .foot{flex:0 0 auto;display:flex;align-items:center;justify-content:center;gap:calc(var(--fs)*.7);flex-wrap:wrap}' +
    // Stats
    '#hdPg .who{flex:0 0 27%;display:flex;flex-direction:column;align-items:center;justify-content:space-evenly;gap:calc(var(--fs)*.4)}' +
    '#hdPg .ph{position:relative;width:min(100%,calc(var(--fs)*9.5));aspect-ratio:4/3;border-radius:50%/48%;overflow:hidden;background:#2a2118 center/cover no-repeat;' +
      'box-shadow:0 0 0 2px #2a1d0c,0 0 0 4px #c99a46,0 0 0 5px #3a2a12,0 0 calc(var(--fs)*1.4) rgba(255,190,80,.35),inset 0 0 calc(var(--fs)*1.2) rgba(0,0,0,.55)}' +
    '#hdPg .ph i{position:absolute;inset:0;display:grid;place-items:center;font:700 calc(var(--fs)*3)/1 var(--display,Georgia,serif);font-style:normal;color:#c99a46}' +
    '#hdPg .xp{width:100%;display:flex;flex-direction:column;gap:calc(var(--fs)*.25);font-size:calc(var(--fs)*.78)}' +
    '#hdPg .xp .ln{display:flex;justify-content:space-between;color:#d9c08a}#hdPg .xp .ln b{color:#f6ead0}' +
    '#hdPg .meter{position:relative;height:calc(var(--fs)*.62);border-radius:999px;background:#120e0a;box-shadow:0 0 0 1px #000,0 0 0 2px #8a6a30;overflow:hidden}' +
    '#hdPg .meter i{position:absolute;left:0;top:0;bottom:0;border-radius:inherit;background:linear-gradient(#fff0b8,#d8a240 55%,#9a6a24)}' +
    '#hdPg .attr{flex:1 1 38%;display:flex;flex-direction:column;justify-content:space-evenly;gap:calc(var(--fs)*.25)}' +
    '#hdPg .ar{display:grid;grid-template-columns:1fr auto auto auto;align-items:center;gap:calc(var(--fs)*.45);padding:calc(var(--fs)*.22) calc(var(--fs)*.55);border-radius:4px;border:1px solid transparent;cursor:pointer}' +
    '#hdPg .ar b{font:700 calc(var(--fs)*1.02)/1.1 var(--display,Georgia,serif);letter-spacing:.03em;color:#efe4cc}' +
    '#hdPg .ar em{font:700 calc(var(--fs)*1.25)/1 var(--display,Georgia,serif);font-style:normal;color:#ffe08a;min-width:calc(var(--fs)*2);text-align:right}' +
    '#hdPg .ar em.up{color:#8fe07a}#hdPg .ar em.dn{color:#ff8a78}' +
    '#hdPg .ar u{text-decoration:none;display:grid;place-items:center;width:calc(var(--fs)*1.5);height:calc(var(--fs)*1.5);border-radius:50%;border:1.5px solid #8a6a30;color:#c99a46;font:700 calc(var(--fs)*1.05)/1 var(--ui,system-ui,sans-serif);background:linear-gradient(#1f1c20,#0d0c10);visibility:hidden}' +
    '#hdPg .ar.sel{border-color:#ffe08a;background:linear-gradient(90deg,rgba(255,200,100,.18),rgba(255,200,100,.05));box-shadow:0 0 calc(var(--fs)*.7) rgba(255,190,80,.35)}' +
    '#hdPg .ar.sel b{color:#fff3c9}#hdPg.pts .ar u{visibility:visible;opacity:.45}#hdPg.pts .ar.sel u{opacity:1;border-color:#ffe08a;color:#ffe08a}' +
    '#hdPg .bat{flex:1 1 35%;display:flex;flex-direction:column;justify-content:space-evenly}' +
    '#hdPg .br{display:flex;justify-content:space-between;align-items:baseline;gap:.6em;padding:calc(var(--fs)*.12) 0;border-bottom:1px solid rgba(201,154,70,.18);font-size:calc(var(--fs)*.88)}' +
    '#hdPg .br:last-child{border-bottom:0}#hdPg .br span{color:#d9c08a}#hdPg .br b{color:#f6ead0;font-weight:700;white-space:nowrap}' +
    '#hdPg .br b.hp{color:#ff9a86}#hdPg .br b.sp{color:#8cc8ff}' +
    // Skills
    '#hdPg .sk{flex:1 1 50%;display:flex;align-items:center;justify-content:center}' +
    '#hdPg .grid{position:relative;width:calc(var(--m)*3 + var(--g)*2);height:calc(var(--mh)*3 + var(--g)*2)}' +
    '#hdPg .sc{position:absolute;width:var(--m);height:var(--mh);display:flex;flex-direction:column;align-items:center;gap:calc(var(--m)*.04);cursor:pointer}' +
    '#hdPg .md{position:relative;width:calc(var(--m)*.78);aspect-ratio:1;border-radius:50%;background:#1b1610 center/cover no-repeat;box-shadow:0 0 0 2px #2a1d0c,0 0 0 calc(var(--m)*.045) #8a6a30,0 4px 10px rgba(0,0,0,.6);transition:transform .12s,box-shadow .12s}' +
    '#hdPg .sc.no .md{filter:grayscale(.75) brightness(.78)}' +
    '#hdPg .sc.sel .md{transform:scale(1.08);box-shadow:0 0 0 2px #2a1d0c,0 0 0 calc(var(--m)*.05) #ffe08a,0 0 calc(var(--m)*.3) rgba(255,190,80,.9)}' +
    '#hdPg .md s{position:absolute;left:-6%;top:-6%;display:grid;place-items:center;width:calc(var(--m)*.27);height:calc(var(--m)*.27);border-radius:50%;text-decoration:none;background:radial-gradient(#fff,#c9c3b6);color:#222;font:800 calc(var(--m)*.15)/1 var(--ui,system-ui,sans-serif);box-shadow:0 0 0 1.5px #c99a46,0 2px 4px rgba(0,0,0,.7)}' +
    '#hdPg .pp{display:flex;gap:calc(var(--m)*.035)}' +
    '#hdPg .pp i{width:calc(var(--m)*.1);height:calc(var(--m)*.1);transform:rotate(45deg);border:1px solid #8a6a30;background:#15110c}' +
    '#hdPg .pp i.on{background:linear-gradient(135deg,#fff0b8,#d8a240);border-color:#ffe08a;box-shadow:0 0 4px rgba(255,190,80,.7)}' +
    '#hdPg .sn{max-width:118%;font:600 calc(var(--m)*.15)/1.1 var(--ui,system-ui,sans-serif);color:#d9c08a;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '#hdPg .sc.sel .sn{color:#fff3c9}' +
    '#hdPg .desc{flex:0 0 auto;padding:calc(var(--fs)*.45) calc(var(--fs)*.9);font:500 calc(var(--fs)*.86)/1.3 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;min-height:calc(var(--fs)*3.4);box-sizing:border-box}' +
    '#hdPg .desc b{font:700 calc(var(--fs)*.98)/1.2 var(--display,Georgia,serif);color:#3a240c}' +
    '#hdPg .desc .dl{float:right;margin-left:1em;font:700 calc(var(--fs)*.78)/1.6 var(--ui,system-ui,sans-serif);color:#6a4a1a}' +
    // phone held upright: the cards stack
    '#hdPg.tall.pgT .main{flex-direction:column}' +
    '#hdPg.tall .who{flex:0 0 auto;flex-direction:row;padding:calc(var(--fs)*.7) calc(var(--fs)*.8) calc(var(--fs)*.5)}' +
    '#hdPg.tall .who .ph{width:calc(var(--fs)*6.2);flex:0 0 auto}' +
    '#hdPg.tall .attr,#hdPg.tall .bat{flex:1 1 auto}' +
    '#hdPg.tall .bat{display:grid;grid-template-columns:1fr 1fr;column-gap:calc(var(--fs)*1);align-content:space-evenly}' +
    '#hdPg.tall .sk{flex:1 1 50%}' +
    // the HUD
    '#hudItems{display:none!important}' +
    '#hdHud{position:fixed;z-index:21;pointer-events:none;box-sizing:border-box;display:flex;align-items:flex-end;gap:calc(var(--h)*.12);padding:0 calc(var(--h)*.18) calc(var(--h)*.08);color:#f6ead0;' +
      'background:linear-gradient(180deg,rgba(10,8,6,0) 0%,rgba(10,8,6,.7) 16%,rgba(10,8,6,.95) 30%,#0b0907 100%);font:700 calc(var(--h)*.2)/1 var(--ui,system-ui,sans-serif)}' +
    '#hdHud[hidden]{display:none}' +
    '#hdHud::before{content:"";position:absolute;left:0;right:0;top:24%;height:1.5px;background:linear-gradient(90deg,transparent,#c99a46 12%,#f6dc93 50%,#c99a46 88%,transparent)}' +
    '#hdHud .hl{position:relative;flex:0 0 auto;width:calc(var(--h)*.62);height:calc(var(--h)*.62);border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 40% 35%,#3a3128,#120e0a 70%);' +
      'box-shadow:0 0 0 2px #2a1d0c,0 0 0 calc(var(--h)*.05) #c99a46,0 0 calc(var(--h)*.2) rgba(255,190,80,.35)}' +
    '#hdHud .hl b{font:700 calc(var(--h)*.27)/1 var(--display,Georgia,serif);background:linear-gradient(#fff3c9,#e7b552 60%,#a8742a);-webkit-background-clip:text;background-clip:text;color:transparent}' +
    '#hdHud .hl i{position:absolute;bottom:-14%;left:50%;transform:translateX(-50%);padding:0 .35em;border-radius:999px;background:#101a33;border:1px solid #c99a46;font:700 calc(var(--h)*.12)/1.35 var(--display,Georgia,serif);font-style:normal;letter-spacing:.08em;color:#f0d38a}' +
    '#hdHud .bars{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:calc(var(--h)*.06);padding-bottom:calc(var(--h)*.02)}' +
    '#hdHud .two{display:flex;gap:calc(var(--h)*.14)}' +
    '#hdHud .bb{position:relative;flex:1 1 50%;height:calc(var(--h)*.3);border-radius:calc(var(--h)*.06);background:#120e0a;box-shadow:0 0 0 1px #000,0 0 0 2.5px #c99a46,0 0 0 3.5px #2a1d0c,inset 0 2px 5px rgba(0,0,0,.8);overflow:hidden}' +
    '#hdHud .bb i{position:absolute;left:0;top:0;bottom:0;transition:width .18s}' +
    '#hdHud .bb.h i{background:linear-gradient(#ff9a7a,#d0301c 45%,#7a140c)}#hdHud .bb.s i{background:linear-gradient(#a8dcff,#2a6ad8 45%,#12306e)}' +
    '#hdHud .bb i::after{content:"";position:absolute;left:0;right:0;top:12%;height:22%;background:rgba(255,255,255,.28);border-radius:999px}' +
    '#hdHud .bb span{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:.35em;font:700 calc(var(--h)*.19)/1 var(--ui,system-ui,sans-serif);color:#fff;text-shadow:0 1px 2px #000,0 0 4px #000;white-space:nowrap}' +
    '#hdHud .bb span em{font-style:normal;opacity:.75;font-size:.85em}' +
    '#hdHud .xb{position:relative;height:calc(var(--h)*.075);border-radius:999px;background:#120e0a;box-shadow:0 0 0 1px #000,0 0 0 2px #8a6a30;overflow:hidden}' +
    '#hdHud .xb i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(#fff0b8,#d8a240 55%,#9a6a24)}' +
    '#hdHud .it{flex:0 0 auto;display:flex;gap:calc(var(--h)*.1);align-items:center;padding-bottom:calc(var(--h)*.04)}' +
    '#hdHud .it span{position:relative;width:calc(var(--h)*.36);height:calc(var(--h)*.36);display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle,#2a2118,#0e0b08 75%);box-shadow:0 0 0 1.5px #8a6a30}' +
    '#hdHud .it span svg{width:72%;height:72%}' +
    '#hdHud .it span b{position:absolute;right:-18%;bottom:-14%;min-width:1.2em;padding:0 .2em;box-sizing:border-box;border-radius:999px;background:#120e0a;border:1px solid #c99a46;font:700 calc(var(--h)*.13)/1.3 var(--ui,system-ui,sans-serif);text-align:center;color:#f6ead0}' +
    '#hdHud .it span.z b{color:#ff8a78}' +
    '#hdHud .orb{flex:0 0 auto;width:calc(var(--h)*.66);height:calc(var(--h)*.66);border-radius:50%;overflow:hidden;background:#120e0a;box-shadow:0 0 0 2px #2a1d0c,0 0 0 calc(var(--h)*.05) #c99a46,0 0 calc(var(--h)*.22) rgba(255,190,80,.35)}' +
    '#hdHud .orb canvas{width:100%;height:100%;display:block;image-rendering:auto}' +
    // v228 (Jordan: "Shield should be animated over hp jar as a light blue force field"): Gandalf's Shield over the Hit Points bar
    '#hdHud .bb.h{transition:box-shadow .3s}#hdHud .bb.h.sh{box-shadow:0 0 0 1px #000,0 0 0 2.5px #9fdcff,0 0 0 3.5px #1c3a5a,0 0 calc(var(--h)*.12 + var(--h)*.18*var(--sf)) rgba(120,200,255,calc(.35 + .5*var(--sf))),inset 0 2px 5px rgba(0,0,0,.8)}' +
    '#hdHud .bb s.sf{position:absolute;left:0;top:0;bottom:0;width:0;text-decoration:none;pointer-events:none;transition:width .2s;background:linear-gradient(rgba(220,245,255,.75),rgba(120,200,255,.55) 45%,rgba(60,140,240,.6));mix-blend-mode:screen}' +
    '#hdHud .bb s.sf::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(115deg,rgba(255,255,255,0) 0 calc(var(--h)*.1),rgba(230,250,255,.55) calc(var(--h)*.13),rgba(255,255,255,0) calc(var(--h)*.16) calc(var(--h)*.34));background-size:calc(var(--h)*1.36) 100%;animation:hdField 1.1s linear infinite}' +
    '#hdHud .bb s.sf::after{content:"";position:absolute;inset:-1px;border-radius:inherit;box-shadow:inset 0 0 calc(var(--h)*.08) rgba(200,240,255,.9);animation:hdPulse 1.6s ease-in-out infinite}' +
    '#hdHud.tall .bb.sh span em{display:none}' +
    '@keyframes hdField{to{background-position:calc(var(--h)*1.36) 0}}@keyframes hdPulse{50%{opacity:.35}}' +
    '#hdHud .bb span b{font:inherit;color:#bfe8ff;margin-left:.2em;text-shadow:0 0 4px rgba(120,200,255,.9),0 1px 2px #000}' +
    '#hdHud .fl i{position:absolute;left:22%;right:22%;bottom:9%;border-radius:0 0 30% 30%;background:linear-gradient(rgba(200,240,255,.85),rgba(70,150,255,.75));box-shadow:0 0 8px rgba(120,200,255,.9);animation:hdPulse 1.6s ease-in-out infinite;pointer-events:none}' +
    '#hdHud.tall .two{flex-direction:column;gap:calc(var(--h)*.07)}#hdHud.tall .bb{flex:0 0 auto;height:calc(var(--h)*.24)}#hdHud.tall .bb span{font-size:calc(var(--h)*.16)}' +
    '#hdHud .fl{position:absolute;bottom:0;display:grid;place-items:center;border-radius:calc(var(--h)*.12) calc(var(--h)*.12) 0 0;background:radial-gradient(circle at 50% 40%,#2a2118,#0b0907 75%);box-shadow:0 0 0 1.5px #8a6a30,0 -2px 8px rgba(0,0,0,.6)}' +
    '#hdHud .fl[hidden]{display:none}#hdHud .fl svg{width:92%;height:auto;max-height:80%}';
  const addCss = () => { if (document.getElementById("hdPagesCss")) return; const s = document.createElement("style"); s.id = "hdPagesCss"; s.textContent = CSS; document.head.appendChild(s); };
  addCss();

  // ---- the backdrop for the Backpack, Forge and Shrine ----
  setInterval(() => {
    for (const id of ["hdBp", "hdSh"]) {
      const e = document.getElementById(id); if (!e || e.hidden) continue;
      const r = e.getBoundingClientRect(); if (!r.width) continue;
      const url = backdrop(r.width, r.height), want = url ? 'url("' + url + '")' : "none";
      if (e.__bg !== want) { e.__bg = want; e.style.setProperty("--hdbg", want); }
      e.classList.toggle("tl", r.height > r.width * 1.05);   // phone held upright: the item page above the boxes
    }
  }, 250);

  // ================= Stats and Skills =================
  let el = null, last = "", shownAt = 0, lastSt = 0, busy = 0, ctx = null;
  const icons = {}, photos = {};
  // where the game draws things on its 240 x 160 page
  const PASS = (k) => [8 + 32 * (k % 3), 24 + 32 * ((k / 3) | 0)];
  const ACT = [[136, 24], [168, 24], [200, 24], [152, 56], [184, 56], [168, 88]];
  // the active skills sit like the game's (3 / 2 / 1), so the d-pad moves the way it looks
  const ACT_AT = [[0, 0], [1, 0], [2, 0], [0.5, 1], [1.5, 1], [1, 2]];
  const pageOk = (f, st) => {
    // the page's title bar is drawn (red for Stats, green-blue for Skills) and bright: not mid-fade
    const ox = (f.w - 240) >> 1, oy = (f.h - 160) >> 1, o = f.off + ((oy + 6) * f.w + ox + 60) * 3, r = f.u8[o], g = f.u8[o + 1], b = f.u8[o + 2];
    return st === 14 ? r > 120 && r > g + 50 : g > 90 && g > r + 30 && b > 60;
  };
  const grabIcons = (st, hid) => {
    const f = frame(); if (!f || !pageOk(f, st)) return false;
    const ox = (f.w - 240) >> 1, oy = (f.h - 160) >> 1;
    if (st === 14) { if (!photos[hid]) photos[hid] = toURL(crop(f, ox + 16, oy + 104, 64, 48), 192, 144); return true; }
    const k0 = hid + ":";
    for (let k = 0; k < 9; k++) if (!icons[k0 + "p" + k]) { const [x, y] = PASS(k); icons[k0 + "p" + k] = medal(f, ox + x, oy + y); }
    for (let k = 0; k < 6; k++) if (!icons[k0 + "a" + k]) { const [x, y] = ACT[k]; icons[k0 + "a" + k] = medal(f, ox + x, oy + y); }
    return true;
  };
  // walk the game's cursor to a box, then (optionally) press A
  const walkTo = (want, done) => {
    if (busy) return; busy = 1; let n = 0;
    const step = () => {
      const v = view(); if (!v || ![14, 15].includes(v.H[v.iw + ST])) { busy = 0; return; }
      const H = v.H, st = H[v.iw + ST], sub = H[v.iw + SUB], cur = H[v.iw + CUR];
      let at, to;
      if (st === 14) { at = [0, cur]; to = [0, want.k]; }
      else {
        const pos = (side, k) => side === 2 ? [k % 3, (k / 3) | 0] : [3.6 + ACT_AT[k][0], ACT_AT[k][1]];
        at = pos(sub, cur); to = pos(want.side, want.k);
      }
      if (at[0] === to[0] && at[1] === to[1]) { busy = 0; if (done) done(); return; }
      if (++n > 14) { busy = 0; return; }
      const dx = to[0] - at[0], dy = to[1] - at[1];
      press(Math.abs(dy) >= 0.75 ? (dy > 0 ? 5 : 4) : dx > 0 ? 7 : 6, 70);
      setTimeout(step, 230);
    };
    step();
  };
  const build = () => {
    el = document.createElement("div"); el.id = "hdPg"; el.className = "hdx"; el.hidden = true;
    (document.getElementById("stage") && false ? document.getElementById("stage") : document.body).appendChild(el);
    el.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      const t = e.target.closest("[data-k],[data-a],[data-s]"); if (!t || !ctx) return;
      if (t.dataset.k) { key(t.dataset.k); return; }
      if (t.dataset.a !== undefined) {   // a Stats row; its - / + place or take back a point
        const k = +t.dataset.a, d = e.target.closest("[data-d]");
        walkTo({ k }, d ? () => press(d.dataset.d === "+" ? 7 : 6, 80) : null);
        return;
      }
      if (t.dataset.s) { const [side, k] = t.dataset.s.split(":").map(Number); walkTo({ side, k }); }
    });
  };
  const hide = () => { window.__hdPgOn = false; if (el && !el.hidden) { el.hidden = true; last = ""; } };
  const pips = (n, max) => { let s = ""; for (let i = 0; i < max; i++) s += '<i' + (i < n ? ' class="on"' : "") + "></i>"; return '<span class="pp">' + s + "</span>"; };
  const nav = (st) => st === 14 ? ['<b class="pill" data-k="L">&#9666; L&nbsp; Skills</b>', '<b class="pill" data-k="R">Backpack &nbsp;R &#9656;</b>']
    : ['<b class="pill" data-k="L">&#9666; L&nbsp; Backpack</b>', '<b class="pill" data-k="R">Stats &nbsp;R &#9656;</b>'];
  setInterval(() => {
    try {
      const v = view(); if (!v) return hide();
      const { H, iw } = v, st = H[iw + ST];
      if (st !== 14 && st !== 15) { lastSt = st; return hide(); }
      const cv = document.getElementById("mpCanvas"); if (!cv) return hide();
      const r = cv.getBoundingClientRect(); if (!r.width) return hide();
      if (!el) build();
      const now = performance.now();
      if (lastSt !== st) { lastSt = st; shownAt = now; }
      const p = H[iw + 0x3F59] & 1, P = iw + 0x3C00 + 0x1AC * p, hid = H[P + 0x19F] & 7, lvl = H[P + 0x19C], sub = H[iw + SUB], cur = H[iw + CUR];
      // the game's own picture first (the cut-outs need it), then the page covers it
      let ready = st === 14 ? !!photos[hid] : !!icons[hid + ":a5"];
      if (!ready && now - shownAt > 350) ready = grabIcons(st, hid);
      if (!ready && now - shownAt < 1200) { window.__hdPgOn = false; if (!el.hidden) { el.hidden = true; last = ""; } return; }
      const tall = r.height > r.width * 1.05;
      const fs = Math.max(9, Math.round(tall ? Math.min(r.width * 0.036, r.height * 0.027) : Math.min(r.height * 0.036, r.width * 0.019)));
      let html = "", k2 = "";
      const head = (sub2) => {
        const n = nav(st);
        return '<div class="top">' + n[0] + '<div class="ttl"><b>' + esc(HERO[hid]) + '</b><div class="orn"></div><i>Level ' + (lvl + 1) + " &middot; " + sub2 + "</i></div>" + n[1] + "</div>";
      };
      if (st === 14) {
        const R = window.__romFull, tbl = (i) => R ? u32(R, 0x628D0 + 4 * i) : 0;
        const xpIn = u32(H, P + 0x178); let xpAll = xpIn; for (let i = 0; i < lvl; i++) xpAll += tbl(i);
        const need = lvl <= 0x31 ? tbl(lvl) : 0, next = need ? need - xpIn : null;
        // Damage, as 0x08027904 (weapon) and 0x08027984 (bonuses) work it out
        const a = u16(H, P + 0xA4), b = u16(H, P + 0xA6), fl = u16(H, P + 0x18C);
        let f1 = (a + b) & 0xFFFF; if (fl & 1) f1 = (f1 + u16(H, P + 0xAC)) & 0xFFFF;
        const t6 = H[P + 0x44] & 15, t7 = H[P + 0x40] & 15, hp = s16(H, P + 0x17C), hpm = s16(H, P + 0xD0);
        let f2 = u16(H, P + 0xAE);
        if (hid === 2 && (fl & 2) && (fl & 4)) f2 += u16(H, P + 0x150);
        if (t6 === 9) f2 += u16(H, P + 0x126);
        for (const t of [t6, t7]) f2 += t < 3 ? u16(H, P + 0x128) : t === 3 ? u16(H, P + 0x12A) : t === 6 ? u16(H, P + 0x12C) : 0;
        if (s16(H, P + 0x130) && hpm > 0 && hp * 100 / hpm <= 25) f2 += u16(H, P + 0x130);
        const str = s16(H, P + 0xC6); if (str > 20) f2 += ((str - 20) >> 2) & 255;
        f2 &= 0xFFFF;
        const dmin = ((f1 >> 1) + f2) & 0xFFFF, dmax = (f1 + f2) & 0xFFFF;
        const pts = H[P + 0x19D], canMove = !!(H[iw + 0x41BC] | H[iw + 0x41BD]);
        const names = ["Strength", "Accuracy", "Health", "Defense", "Courage"];
        const rows = names.map((nm, i) => {
          const val = s16(H, P + 0xC6 + 2 * i), pend = H[iw + 0x1CE8 + 12 * p + 10 - 2 * i];
          return '<div class="ar' + (i === cur ? " sel" : "") + '" data-a="' + i + '"><b>' + nm + '</b><u data-d="-">&minus;</u><em class="' + (val > pend ? "up" : val < pend ? "dn" : "") + '">' + val + '</em><u data-d="+">+</u></div>';
        }).join("");
        const sp = s16(H, P + 0x17E), spm = s16(H, P + 0xD2), z = (x) => Math.max(0, x);
        const bat = [["Hit Points", '<b class="hp">' + z(hp) + " / " + z(hpm) + "</b>"], ["Spirit Points", '<b class="sp">' + z(sp) + " / " + z(spm) + "</b>"],
          ["Damage", "<b>" + dmin + " &ndash; " + dmax + "</b>"], ["Melee Armor", "<b>" + z(s16(H, P + 0xBE)) + "</b>"], ["Missile Armor", "<b>" + u16(H, P + 0xC0) + "</b>"],
          ["To Hit", "<b>" + s16(H, P + 0xC8) + "%</b>"], ["Dodge", "<b>" + z(s16(H, P + 0xFC)) + "%</b>"], ["Shield Block", "<b>" + s16(H, P + 0x100) + "%</b>"]]
          .map(([n, x]) => '<div class="br"><span>' + n + "</span>" + x + "</div>").join("");
        const ph = photos[hid];
        html = head("Stats") +
          '<div class="main"><div class="pc who"><h4>Hero</h4><div class="ph" style="' + (ph ? "background-image:url(" + ph + ")" : "") + '">' + (ph ? "" : "<i>" + esc(HERO[hid][0]) + "</i>") + "</div>" +
          '<div class="xp"><div class="ln"><span>Experience</span><b>' + xpAll + '</b></div><div class="meter"><i style="width:' + (need ? Math.min(100, xpIn * 100 / need) : 100).toFixed(1) + '%"></i></div><div class="ln"><span>Next Level</span><b>' + (next === null ? "&ndash;" : next) + "</b></div></div></div>" +
          '<div class="pc attr"><h4>Attributes</h4>' + rows + "</div>" +
          '<div class="pc bat"><h4>In Battle</h4>' + bat + "</div></div>" +
          '<div class="foot"><span class="cp' + (pts ? " hot" : "") + '">Attribute points <em>' + pts + "</em></span>" +
          (canMove ? '<span class="cp">&#9666; &#9656; take back or place a point</span>' : "") + '<b class="pill" data-k="B"><u>B</u>Close</b></div>';
        el.classList.toggle("pts", canMove);
        k2 = [st, cur, pts, canMove, html.length, xpAll, hp, sp, dmin, dmax].join("/");
      } else {
        const pts = H[P + 0x19E], slots = [H[P + 0x191], H[P + 0x192], H[P + 0x193]];
        const pass = []; for (let k = 0; k < 9; k++) pass.push(H[iw + 0x6A10 + k]);
        // the focused skill: the game's own words with its @1 (level needed or "Max") and @2 (Spirit) filled in
        const tp = gba(v, u32(H, iw + 0x2160));
        let words = tp >= 0 ? cstr(H, tp, 400) : "";
        const a1 = cstr(H, iw + 0x1B90, 30), a2 = cstr(H, iw + 0x1BD0, 30);
        words = words.replace(/@1/g, a1).replace(/@2/g, a2);
        const m = /^(.*?) \((?:Level|level) ([^)]*)\)\s*-?\s*(.*)$/.exec(words);
        const fName = m ? m[1] : skillName(words), need = m ? m[2] : "", rest = m ? m[3] : words.replace(/^.*? - /, "");
        const side = sub === 1 ? 1 : 2;
        const cell = (sd, k) => {
          const lv = sd === 2 ? H[P + 0x161 + k] : H[P + 0x16A + k] << 24 >> 24, max = (sd === 2 && k === 8) || (sd === 1 && k === 5) ? 1 : 5;
          const nm = sd === 2 ? skillName(text(482 + pass[k])) : skillName(text(517 + 6 * hid + k));
          const ic = icons[hid + ":" + (sd === 2 ? "p" : "a") + k], sel = side === sd && cur === k;
          const badge = sd === 1 ? ["A", "B", "R"].filter((_, j) => slots[j] === k).join("") : "";
          const at = sd === 2 ? [k % 3, (k / 3) | 0] : ACT_AT[k];
          return '<div class="sc' + (sel ? " sel" : "") + (lv > 0 ? "" : " no") + '" data-s="' + sd + ":" + k + '" style="left:calc(' + at[0] + ' * (var(--m) + var(--g)));top:calc(' + at[1] + ' * (var(--mh) + var(--g)))">' +
            '<div class="md" style="' + (ic ? "background-image:url(" + ic + ")" : "") + '">' + (badge ? "<s>" + badge + "</s>" : "") + "</div>" + pips(Math.max(0, lv), max) + '<div class="sn">' + esc(sel ? fName || nm : nm) + "</div></div>";
        };
        let P2 = "", A2 = "";
        for (let k = 0; k < 9; k++) P2 += cell(2, k);
        for (let k = 0; k < 6; k++) A2 += cell(1, k);
        const lvNow = side === 2 ? H[P + 0x161 + cur] : H[P + 0x16A + cur] << 24 >> 24, maxNow = (side === 2 && cur === 8) || (side === 1 && cur === 5) ? 1 : 5;
        const needTxt = /^\d+$/.test(need) ? (lvNow >= maxNow ? "" : "Next level at hero level " + need) : need === "Max" || lvNow >= maxNow ? "Mastered" : need;
        html = head("Skills") +
          '<div class="main"><div class="pc sk"><h4>Passive</h4><div class="grid">' + P2 + '</div></div><div class="pc sk"><h4>Active</h4><div class="grid">' + A2 + "</div></div></div>" +
          '<div class="parch desc"><span class="dl">Level ' + Math.max(0, lvNow) + " of " + maxNow + (needTxt ? " &middot; " + esc(needTxt) : "") + "</span><b>" + esc(fName) + "</b> &mdash; " + esc(rest) + "</div>" +
          '<div class="foot"><span class="cp' + (pts ? " hot" : "") + '">Skill points <em>' + pts + "</em></span>" +
          '<b class="pill go' + (pts && lvNow < maxNow ? "" : " off") + '" data-k="A"><u>A</u>Learn</b><b class="pill" data-k="B"><u>B</u>Close</b></div>';
        el.classList.remove("pts");
        k2 = [st, sub, cur, pts, words, slots.join(), Array.from(H.slice(P + 0x161, P + 0x170)).join(), !!icons[hid + ":a5"]].join("/");
      }
      const key2 = [k2, r.left, r.top, r.width, r.height, !!photos[hid]].join("|");
      window.__hdPgOn = true;
      if (key2 === last && !el.hidden) return;
      last = key2;
      ctx = { st };
      el.style.left = r.left + "px"; el.style.top = r.top + "px"; el.style.width = r.width + "px"; el.style.height = r.height + "px";
      el.style.setProperty("--fs", fs + "px");
      el.classList.toggle("tall", tall);
      el.classList.toggle("pgT", st === 14); el.classList.toggle("pgS", st === 15);
      const url = backdrop(r.width, r.height), want = url ? 'url("' + url + '")' : "none";
      if (el.__bg !== want) { el.__bg = want; el.style.setProperty("--hdbg", want); }
      el.innerHTML = html;
      if (st === 15) {
        // medallion size from the room the two cards have
        const card = el.querySelector(".pc.sk"), dsc = el.querySelector(".desc");
        if (card) {
          const cw = card.clientWidth - fs * 1.6, ch = card.clientHeight - fs * 1.4;
          const m = Math.max(24, Math.min(cw / 3.3, ch / 3.3 / 1.24));
          el.style.setProperty("--m", m.toFixed(1) + "px"); el.style.setProperty("--mh", (m * 1.24).toFixed(1) + "px"); el.style.setProperty("--g", (m * 0.12).toFixed(1) + "px");
        }
        if (dsc && dsc.scrollHeight > dsc.clientHeight + 2) dsc.style.fontSize = "calc(var(--fs)*.76)";
      }
      el.hidden = false;
    } catch (e) { if (el) el.hidden = true; window.__hdPgOn = false; }
  }, 80);

  // ================= the HUD =================
  const LEAF = (c) => '<svg viewBox="0 0 16 16"><path d="M3 13.5C2.5 7 7 2.5 13.5 2.5 13.5 9 9 13.5 3 13.5z" fill="' + c[0] + '" stroke="#0b0806" stroke-width="1"/><path d="M3.2 13.3 11 5.3" stroke="' + c[1] + '" stroke-width="1.1" fill="none"/></svg>';
  const FLASK = (c) => '<svg viewBox="0 0 16 16"><path d="M6 1.5h4v1.6l-.6.7v2.4l3.4 5.2a2.2 2.2 0 0 1-1.8 3.4H5a2.2 2.2 0 0 1-1.8-3.4l3.4-5.2V3.8L6 3.1z" fill="' + c[0] + '" stroke="#0b0806" stroke-width="1"/><path d="M4.6 10.4h6.8l1 1.6a1.2 1.2 0 0 1-1 1.8H4.6a1.2 1.2 0 0 1-1-1.8z" fill="' + c[1] + '"/></svg>';
  const GREY = ["#4a4038", "#2a241e"];
  let hud = null, hudKey = "", hudItemsKey = "", orbT = 0;
  const hudBuild = () => {
    hud = document.createElement("div"); hud.id = "hdHud"; hud.className = "hdx"; hud.hidden = true;
    hud.innerHTML = '<div class="hl"><b>1</b><i>LV</i></div><div class="bars"><div class="two"><div class="bb h"><i></i><s class="sf"></s><span></span></div><div class="bb s"><i></i><span></span></div></div><div class="xb"><i></i></div></div>' +
      '<div class="it"></div><div class="orb"><canvas width="88" height="88"></canvas></div><div class="fl" hidden></div>';
    document.body.appendChild(hud);
  };
  const hudHide = () => { if (hud && !hud.hidden) { hud.hidden = true; hudKey = ""; } };
  setInterval(() => {
    try {
      const v = view(); if (!v || !document.body.classList.contains("playing")) return hudHide();
      const { H, iw } = v; if (H[iw + ST] !== 1) return hudHide();
      if (window.__hdPgOn || window.__hdBpOn || window.__hdShopOn) return hudHide();
      const cv = document.getElementById("mpCanvas"); if (!cv) return hudHide();
      const r = cv.getBoundingClientRect(); if (!r.width || !r.height) return hudHide();
      if (!hud) hudBuild();
      const tall = r.height > r.width * 1.05;
      const h = Math.round(Math.max(56, Math.min(r.height * (tall ? 0.16 : 0.2), r.width * 0.22)));
      const pos = [r.left, r.bottom, r.width, h, tall].join("/");
      if (pos !== hudKey) {
        hudKey = pos;
        hud.style.left = r.left + "px"; hud.style.width = r.width + "px"; hud.style.top = (r.bottom - h) + "px"; hud.style.height = h + "px";
        hud.style.setProperty("--h", h + "px"); hud.classList.toggle("tall", tall);
      }
      const p = H[iw + 0x3F59] & 1, P = iw + 0x3C00 + 0x1AC * p, lvl = H[P + 0x19C];
      const hp = Math.max(0, s16(H, P + 0x17C)), hpm = Math.max(1, s16(H, P + 0xD0)), sp = Math.max(0, s16(H, P + 0x17E)), spm = Math.max(1, s16(H, P + 0xD2));
      const R = window.__romFull, need = R && lvl <= 0x31 ? u32(R, 0x628D0 + 4 * lvl) : 0, xp = u32(H, P + 0x178);
      const lv = hud.firstChild, bb = hud.querySelectorAll(".bb"), xb = hud.querySelector(".xb i");
      lv.firstChild.textContent = String(lvl + 1);
      // Gandalf's Shield (gandalf-shield.js: window.__gsShown = { S, max, frac } for the local hero)
      const gs = window.__gsShown, S = gs && gs.S > 0 ? gs.S : 0, sf = S ? Math.max(0.05, Math.min(1, gs.frac)) : 0;
      bb[0].classList.toggle("sh", S > 0); bb[0].style.setProperty("--sf", sf.toFixed(2));
      bb[0].children[1].style.width = (sf * 100).toFixed(1) + "%";
      bb[0].firstChild.style.width = Math.min(100, hp * 100 / hpm).toFixed(1) + "%"; bb[0].lastChild.innerHTML = hp + "<em>/ " + hpm + "</em>" + (S ? "<b>&#9672; " + S + "</b>" : "");
      bb[1].firstChild.style.width = Math.min(100, sp * 100 / spm).toFixed(1) + "%"; bb[1].lastChild.innerHTML = sp + "<em>/ " + spm + "</em>";
      xb.style.width = (need ? Math.min(100, xp * 100 / need) : 100).toFixed(1) + "%";
      // Ent Water and Kingsfoil (P+0x1A9 bit 0, P+0x1AA low / high nibble), as the old corner icons had them
      const ent = H[P + 0x1A9] & 1, kf = H[P + 0x1AA], fresh = kf & 15, dried = kf >> 4, ik = [ent, fresh, dried].join();
      if (ik !== hudItemsKey) {
        hudItemsKey = ik;
        const one = (name, svg, n) => '<span title="' + name + '"' + (n ? "" : ' class="z"') + ">" + svg + "<b>" + n + "</b></span>";
        hud.querySelector(".it").innerHTML = one("Ent Water", FLASK(ent ? ["#7cc8e8", "#3a9a5a"] : GREY), ent) +
          one("Fresh Kingsfoil", LEAF(fresh ? ["#5fc444", "#2a6a1e"] : GREY), fresh) + one("Dried Kingsfoil", LEAF(dried ? ["#b8943e", "#6a5020"] : GREY), dried);
      }
      // the game's XP vial (Gandalf's Shield fills it light blue) stands taller than the HUD on a phone held upright: an HD flask goes over it there
      const gv = window.__gbaView, f0 = frame(), fl = hud.querySelector(".fl");
      let lamp = null;
      if (gv && f0 && gv.w === f0.w && gv.h === f0.h && gv.sw > 0 && gv.sh > 0) {
        const tx = (x) => (gv.dest[0] + (x - gv.sx) / gv.sw * gv.dest[2]) / gv.CW * r.width, ty = (y) => (gv.dest[1] + (y - gv.sy) / gv.sh * gv.dest[3]) / gv.CH * r.height;
        const x0 = (f0.w - 240) >> 1, yb = f0.h - (window.__hudB || 0), top = ty(yb - 35);
        if (top < r.height - h * 0.78) lamp = [tx(x0), top, tx(x0 + 21) - tx(x0)];
      }
      const lk = lamp ? lamp.map(Math.round).join() + ":" + ent : "";
      if (lk !== fl.__k) {
        fl.__k = lk; fl.hidden = !lamp;
        hud.style.paddingLeft = "";
        if (lamp) {
          const pad = 4, L = Math.max(0, lamp[0] - pad), W = lamp[2] + pad * 2;
          fl.style.left = L + "px"; fl.style.width = W + "px"; fl.style.height = (r.height - lamp[1] + pad) + "px"; fl.innerHTML = FLASK(["#2a3a2a", "#1a241a"]) + "<i></i>";
          if (L < h) hud.style.paddingLeft = Math.round(L + W + h * 0.12) + "px";   // the level badge goes after it
        }
        hudItemsKey = "";
      }
      { const vi = !fl.hidden && fl.querySelector("i"); if (vi) { vi.style.height = (sf * 72).toFixed(1) + "%"; vi.style.display = sf ? "" : "none"; } }
      // the game's skill orb, cut out of its own HUD (bottom right of the 240-wide strip) and drawn bigger
      const now = performance.now();
      if (now - orbT > 120) {
        orbT = now;
        const f = frame();
        if (f) {
          const x0 = (f.w - 240) >> 1, yb = f.h - (window.__hudB || 0), im = crop(f, x0 + 219, yb - 23, 22, 22), c = hud.querySelector(".orb canvas"), x = c.getContext("2d");
          for (let j = 0; j < 22; j++) for (let i = 0; i < 22; i++) { const nx = (i - 10.5) / 9.6, ny = (j - 10.5) / 9.6; if (nx * nx + ny * ny > 1) im.data[(j * 22 + i) * 4 + 3] = 0; }
          const big = epx(epx(im)), t = document.createElement("canvas"); t.width = big.width; t.height = big.height; t.getContext("2d").putImageData(big, 0, 0);
          x.clearRect(0, 0, 88, 88); x.imageSmoothingQuality = "high"; x.drawImage(t, 0, 0, 88, 88);
        }
      }
      hud.hidden = false;
    } catch (e) { if (hud) hud.hidden = true; }
  }, 100);
})();
