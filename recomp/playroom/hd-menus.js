// HD menus (Jordan, 2026-11-20: "Modernize and update all menus", with three example pictures: dark stone and gold,
// a painted sky with a volcano and a white castle by a waterfall, navy banners with the white tree, glowing gold-edged
// menu bars with icons, and the level goal on parchment).
// The page draws the game's own menus over the picture while they are open, from the game's state and cursor, so
// the game keeps running them (buttons, keyboard and pads all still work, and the page follows the cursor):
//   state 5  (0x030041B0) title menu: New Game, Load Game, Multiplayer, Options, GCN Link, Bonus Maps
//   state 16              pause menu: Save Game, Options, Artifacts, Quit Game, and the level goal. The game draws the
//                         goal one line per frame through a line buffer at IWRAM 0x03007D4C, so the page reads that
//                         buffer every few ms for the first moments of the pause and keeps each new line.
//   cursor 0x030041B8 in both.
//   state 9  save slots (Load Game / Save Game, [0x030041B4] = 1 or 3 when saving): four parchment cards in an open book,
//            slot cursor 0x030041BC (0 1 / 2 3), sub 0x030041C0 = 0 for the list. Each card reads the slot header
//            the game keeps at IWRAM 0x03005630 + 0x70 * slot (current page): + 0x65 hero << 4 (as 0x080311E4 reads it), + 0x5C level - 1,
//            + 0x68 level screen, named like the Story map (window.__lvName). Page 2 flips stay the page's Page button.
//   state 6  Options: Music / SFX Volume, Auto Healing, Fast Discard, Difficulty, Credits. Values at IWRAM 0x03002080 + cursor
//            (the cursor skips 2), changed with Left / Right like a player would.
//   Other screens (hero pick, Artifacts, questions inside a menu) are the
//   game's own for now: the overlay only shows while the game's menu sub-state is the plain list (MENU_SUB).
// Tapping a bar moves the game's cursor there with Up / Down presses and then presses A, as a player would, so it
// works the same in 1-player, P2 and online games (presses travel with the buttons).
(() => {
  const ST = 0x41B0, SUB = 0x41C0, CUR = 0x41B8, GOAL = 0x7D4C;
  const ICON = {
    swords: '<path d="M4 4l9 9M20 4l-9 9M3 6l3-3M18 3l3 3M8 15l-3 3 1 1M16 15l3 3-1 1M6 19l-2 2M18 19l2 2M11 11l-2 2 2 2M13 11l2 2-2 2"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/>',
    group: '<circle cx="12" cy="8" r="3"/><circle cx="5.5" cy="9.5" r="2.2"/><circle cx="18.5" cy="9.5" r="2.2"/><path d="M6.5 19c0-3.5 2.5-6 5.5-6s5.5 2.5 5.5 6M1.5 18c0-2.6 1.6-4.4 4-4.6M22.5 18c0-2.6-1.6-4.4-4-4.6"/>',
    gear: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/><circle cx="12" cy="12" r="6.6"/>',
    cube: '<path d="M12 2.5l8.5 4.8v9.4L12 21.5l-8.5-4.8V7.3z"/><path d="M3.5 7.3L12 12l8.5-4.7M12 12v9.5"/>',
    scroll: '<path d="M6 4h12a2 2 0 0 1 2 2v1H8M6 4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7"/><path d="M12 9l1 2.2 2.4.3-1.8 1.6.5 2.4-2.1-1.2-2.1 1.2.5-2.4-1.8-1.6 2.4-.3z"/>',
    disk: '<path d="M4 4h13l3 3v13H4z"/><path d="M8 4v5h8V4M7 20v-6h10v6"/>',
    gem: '<path d="M12 2.5l5 9.5-5 9.5-5-9.5z"/><path d="M7 12h10M12 2.5v19"/>',
    exit: '<path d="M14 4H6v16h8"/><path d="M11 12h10M17 8l4 4-4 4"/>',
    music: '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    sound: '<path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/>',
    heart: '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20z"/><path d="M12 10.5v5M9.5 13h5"/>',
    bolt: '<path d="M13 2.5L5 13.5h6l-1 8 8-11h-6z"/>',
    gate: '<path d="M5 21V10a7 7 0 0 1 14 0v11"/><path d="M12 3v18M8.5 8.5l7 7M15.5 8.5l-7 7"/><path d="M3 21h18"/>',
    hill: '<path d="M2 20l7-10 4 5 3-3 6 8z"/><path d="M8 10.5l1-3.5 1 3.5M7 7h4"/>',
    tower: '<path d="M7 21V7h10v14M5 7V4h2v1.5h2V4h2v1.5h2V4h2v1.5h2V4h2v3z"/><path d="M10 21v-4a2 2 0 0 1 4 0v4M3 21h18"/>',
    tree: '<path d="M12 21v-8M12 13l-4-3M12 15l4-3"/><path d="M12 3c4 0 7 2.5 7 6 0 2.5-2 4.5-5 4.5h-4C7 13.5 5 11.5 5 9c0-3.5 3-6 7-6z"/><path d="M8 21h8"/>',
    shield: '<path d="M12 2.5l8 3v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10v-6z"/><path d="M12 6v12M8 10h8"/>',
  };
  const MENUS = {
    5: { head: "", items: [["New Game", "swords"], ["Load Game", "folder"], ["Multiplayer", "group"], ["Options", "gear"], ["Bonus Maps", "scroll", 5]], skip: 4 },
    // Bonus Maps' path picker: map cursor 0x030041B8 (sub 0), then its level list (sub 1) and difficulty (sub 2), both at 0x030041B4
    24: { head: "Choose Your Path", items: [] },
    // Multiplayer's own GBA link screen (the page has its own P2 and online games)
    23: { head: "", items: [] },
    9: { head: "", items: [] },
    // Options: the cursor skips 2, each setting's value is at IWRAM 0x03002080 + its cursor (volumes 0-10, 0 = Off;
    // Auto Healing and Fast Discard 0 Off / 1 On; Difficulty 0 Normal, 1 Hard, 2 Grueling). Left / Right change them.
    6: { head: "Options", items: [["Music Volume", "music", 0, "vol"], ["SFX Volume", "sound", 1, "vol"], ["Auto Healing", "heart", 3, "on"], ["Fast Discard", "bolt", 4, "on"], ["Difficulty", "shield", 5, "diff"], ["Credits", "scroll", 6]] },
    16: { head: "Game Paused", items: [["Save Game", "disk"], ["Options", "gear"], ["Artifacts", "gem"], ["Quit Game", "exit"]], goal: true },
  };
  const MENU_SUB = { 5: [0, 1, 2, 3], 16: [0, 1], 9: [0, 1, 3, 4], 6: [0], 24: [0, 1, 2], 23: [0] };
  const MAPS = [["Moria", "Dwarf Halls", "gate"], ["Weathertop", "Amon S\u00fbl", "hill"], ["Helm's Deep", "Hornburg", "tower"], ["Fangorn Forest", "Entwood", "tree"]];
  const OPT = 0x2080, DIFF = ["Normal", "Hard", "Grueling"];
  const HERO = [["Frodo", "#3d5f9a"], ["Legolas", "#3f6a2a"], ["Aragorn", "#5a3a20"], ["Gandalf", "#4a4844"], ["\u00c9owyn", "#7a2a2a"], ["Gimli", "#9a2a1e"], ["Sam", "#5a4a22"], ["Sm\u00e9agol", "#4d5a3a"]];
  const TREE = '<svg class="tr" viewBox="0 0 120 130" aria-hidden="true"><g fill="currentColor"><path d="M60 4l1.6 4.2 4.4.3-3.4 2.8 1.1 4.3L60 13.2l-3.7 2.4 1.1-4.3-3.4-2.8 4.4-.3z"/><circle cx="38" cy="16" r="1.8"/><circle cx="82" cy="16" r="1.8"/><circle cx="24" cy="28" r="1.5"/><circle cx="96" cy="28" r="1.5"/></g><g fill="none" stroke="currentColor" stroke-linecap="round"><path stroke-width="5" d="M60 124V52"/><path stroke-width="3" d="M60 84C48 76 40 66 36 52M60 84c12-8 20-18 24-32M60 70C52 62 48 50 48 38M60 70c8-8 12-20 12-32M60 60V30"/><path stroke-width="2" d="M36 52c-8-4-14-10-16-18M36 52c-4-8-4-14-2-20M84 52c8-4 14-10 16-18M84 52c4-8 4-14 2-20M48 38c-6-4-8-10-8-16M48 38c0-8 2-12 6-16M72 38c6-4 8-10 8-16M72 38c0-8-2-12-6-16M60 30c-3-4-4-6-4-10M60 30c3-4 4-6 4-10M60 96c-10 0-22-2-30-8M60 96c10 0 22-2 30-8"/><path stroke-width="2.4" d="M60 120c-6 4-14 6-24 6M60 120c6 4 14 6 24 6M60 116c-2 4-6 8-12 10M60 116c2 4 6 8 12 10"/></g></svg>';
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // ---- the painted backdrop: dusk sky, clouds, a volcano, mountains, a white castle by a waterfall, stone pillars ----
  let rnd = 1;
  const rand = () => { rnd = (rnd * 16807) % 2147483647; return (rnd - 1) / 2147483646; };
  function paint(cv) {
    // places are fractions of the width / height; sizes follow U so shapes keep their look at any aspect
    const W = cv.width, H = cv.height, x = cv.getContext("2d"), U = Math.min(W, H * 1.6); rnd = 7;
    const sky = x.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, "#141a2c"); sky.addColorStop(0.3, "#3a3049"); sky.addColorStop(0.5, "#a3584a"); sky.addColorStop(0.62, "#efa25c"); sky.addColorStop(0.7, "#f6c27a"); sky.addColorStop(1, "#2a2230");
    x.fillStyle = sky; x.fillRect(0, 0, W, H);
    const sun = x.createRadialGradient(W * 0.45, H * 0.64, 0, W * 0.45, H * 0.64, U * 0.6);
    sun.addColorStop(0, "rgba(255,214,140,0.85)"); sun.addColorStop(0.3, "rgba(255,170,90,0.35)"); sun.addColorStop(1, "rgba(255,150,80,0)");
    x.fillStyle = sun; x.fillRect(0, 0, W, H);
    // clouds: soft banks, dark on top and lit from below (drawn as scaled circles so the edges fade out)
    for (let i = 0; i < 90; i++) {
      const cx = rand() * W, cy = H * (0.03 + rand() * 0.45), r = U * (0.03 + rand() * 0.07), lit = cy / H;
      x.save(); x.translate(cx, cy); x.scale(2.2, 0.6);
      const g = x.createRadialGradient(0, -r * 0.2, 0, 0, 0, r);
      g.addColorStop(0, `rgba(${46 + 60 * lit | 0},${36 + 30 * lit | 0},52,0.5)`); g.addColorStop(0.6, `rgba(${150 + 100 * lit | 0},${80 + 50 * lit | 0},64,${0.15 + 0.25 * lit})`); g.addColorStop(1, "rgba(120,70,70,0)");
      x.fillStyle = g; x.beginPath(); x.arc(0, 0, r, 0, Math.PI * 2); x.fill(); x.restore();
    }
    const ridge = (y0, amp, col, rough, seed) => {
      rnd = seed; x.fillStyle = col; x.beginPath(); x.moveTo(0, H);
      let y = y0, step = Math.max(3, U / 120);
      for (let px = 0; px <= W + step; px += step) { y += (rand() - 0.5) * rough; y += (y0 - y) * 0.08; x.lineTo(px, y - amp * Math.sin(px / U * 3.1 + seed)); }
      x.lineTo(W, H); x.closePath(); x.fill();
    };
    ridge(H * 0.66, U * 0.03, "rgba(92,70,96,0.75)", U * 0.02, 3);
    // volcano on the left with a glowing crater, lava runs and smoke
    const vx = W * 0.22, vy = H * 0.62 - U * 0.2, vb = H * 0.62 + U * 0.08;
    const vg = x.createLinearGradient(0, vy, 0, vb); vg.addColorStop(0, "#3b2a2c"); vg.addColorStop(1, "#1d1518");
    x.fillStyle = vg; x.beginPath(); x.moveTo(vx - U * 0.025, vy); x.lineTo(vx + U * 0.025, vy); x.lineTo(vx + U * 0.22, vb); x.lineTo(vx - U * 0.2, vb); x.closePath(); x.fill();
    const cr = x.createRadialGradient(vx, vy, 0, vx, vy, U * 0.07); cr.addColorStop(0, "rgba(255,190,90,0.95)"); cr.addColorStop(0.35, "rgba(255,90,30,0.55)"); cr.addColorStop(1, "rgba(255,60,20,0)");
    x.fillStyle = cr; x.beginPath(); x.arc(vx, vy, U * 0.07, 0, Math.PI * 2); x.fill();
    x.strokeStyle = "rgba(255,110,40,0.8)"; x.lineCap = "round"; x.lineWidth = Math.max(1, U * 0.004);
    for (let i = 0; i < 5; i++) { x.beginPath(); let px = vx + (rand() - 0.5) * U * 0.03, py = vy + 2; x.moveTo(px, py); for (let k = 0; k < 7; k++) { px += (i - 2) * U * 0.006 + (rand() - 0.5) * U * 0.008; py += (vb - vy) * 0.08; x.lineTo(px, py); } x.stroke(); }
    for (let i = 0; i < 18; i++) { const sx = vx + U * 0.006 * i, sy = vy - U * 0.015 - i * U * 0.014, sr = U * (0.018 + i * 0.002); const sg = x.createRadialGradient(sx, sy, 0, sx, sy, sr); sg.addColorStop(0, "rgba(60,48,56,0.35)"); sg.addColorStop(1, "rgba(60,48,56,0)"); x.fillStyle = sg; x.beginPath(); x.arc(sx, sy, sr, 0, Math.PI * 2); x.fill(); }
    ridge(H * 0.74, U * 0.025, "#2c2433", U * 0.025, 11);
    // the white city on a cliff to the right, a waterfall and mist
    const base = H * 0.7, cl = W * 0.66;
    x.fillStyle = "#2a2a2e"; x.beginPath(); x.moveTo(cl - U * 0.05, H * 0.9); x.lineTo(cl - U * 0.015, base - U * 0.02); x.lineTo(W, base - U * 0.03); x.lineTo(W, H * 0.9); x.closePath(); x.fill();
    const tower = (tx, tw, th) => {
      const top = base - U * 0.02 - th, g = x.createLinearGradient(tx, 0, tx + tw, 0); g.addColorStop(0, "#f3efe6"); g.addColorStop(1, "#b9b3aa");
      x.fillStyle = g; x.fillRect(tx, top, tw, th + U * 0.02);
      x.fillStyle = "#d8d1c6"; x.beginPath(); x.moveTo(tx - tw * 0.15, top); x.lineTo(tx + tw / 2, top - tw * 1.3); x.lineTo(tx + tw * 1.15, top); x.closePath(); x.fill();
      x.fillStyle = "rgba(255,206,120,0.9)"; const wh = Math.max(1, U * 0.006);
      for (let k = 1; k * U * 0.025 < th; k++) x.fillRect(tx + tw * 0.4, top + k * U * 0.025, Math.max(1, tw * 0.2), wh);
    };
    [[0.0, 0.016, 0.06], [0.025, 0.02, 0.12], [0.055, 0.016, 0.08], [0.085, 0.014, 0.05], [0.11, 0.02, 0.09], [0.14, 0.015, 0.06], [0.165, 0.013, 0.035]]
      .forEach(([a, b, c]) => { const tx = cl + U * a; if (tx < W) tower(tx, U * b, U * c); });
    const wf = x.createLinearGradient(0, base, 0, H * 0.9); wf.addColorStop(0, "rgba(235,245,255,0.95)"); wf.addColorStop(1, "rgba(200,220,240,0.45)");
    x.fillStyle = wf; for (const [a, w] of [[0.07, 0.012], [0.105, 0.008]]) x.fillRect(cl + U * a, base, U * w, H * 0.9 - base);
    const mist = x.createRadialGradient(cl + U * 0.09, H * 0.88, 0, cl + U * 0.09, H * 0.88, U * 0.18); mist.addColorStop(0, "rgba(240,240,245,0.5)"); mist.addColorStop(1, "rgba(240,240,245,0)");
    x.fillStyle = mist; x.fillRect(0, 0, W, H);
    // dark forest at the bottom
    rnd = 23; x.fillStyle = "#14161a";
    const tw = U * 0.012; for (let px = 0; px < W + tw; px += tw) { const th = U * (0.03 + rand() * 0.05); x.beginPath(); x.moveTo(px - tw, H); x.lineTo(px, H * 0.9 - th); x.lineTo(px + tw, H); x.fill(); }
    x.fillRect(0, H * 0.93, W, H * 0.07);
    // stone pillars on both sides with torch light
    const pw = Math.max(U * 0.06, W * 0.05);
    for (const side of [0, 1]) {
      const x0 = side ? W - pw : 0, g = x.createLinearGradient(x0, 0, x0 + pw, 0);
      g.addColorStop(side ? 1 : 0, "#3a3732"); g.addColorStop(side ? 0 : 1, "#16140f");
      x.fillStyle = g; x.fillRect(x0, 0, pw, H);
      x.strokeStyle = "rgba(0,0,0,0.45)"; x.lineWidth = 1;
      for (let y = 0, r = 0; y < H; y += pw * 0.55, r++) { const o = x0 + pw * (r & 1 ? 0.5 : 0.25); x.beginPath(); x.moveTo(x0, y); x.lineTo(x0 + pw, y); x.moveTo(o, y); x.lineTo(o, y + pw * 0.55); x.stroke(); }
      const fx = side ? W - pw * 0.5 : pw * 0.5, tg = x.createRadialGradient(fx, H * 0.22, 0, fx, H * 0.22, U * 0.2);
      tg.addColorStop(0, "rgba(255,170,70,0.5)"); tg.addColorStop(1, "rgba(255,150,60,0)"); x.fillStyle = tg; x.fillRect(0, 0, W, H);
    }
    const vign = x.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.max(W, H) * 0.75);
    vign.addColorStop(0, "rgba(0,0,0,0)"); vign.addColorStop(1, "rgba(0,0,0,0.55)"); x.fillStyle = vign; x.fillRect(0, 0, W, H);
  }

  window.__hdPaint = paint;   // v224: the HD Stats / Skills pages paint the same backdrop
  let lastOn = 0; const QUIT_YES = 0;
  let el = null, bg = null, lastKey = "", busy = 0, shownAt = 0, skipHold = 0, lastCur = -1;
  // the level goal, caught line by line as the game draws it into its line buffer
  let goalLines = [], goalSt = 0, goalT = 0;
  // a slow device can run two game frames between reads and miss the first line: a goal that doesn't start with a
  // capital is a fragment, so the page shows the whole goal it caught before (kept by its last line) or nothing
  let goalMem = {}; try { goalMem = JSON.parse(localStorage.getItem("rotk-goals") || "{}") || {}; } catch (e) {}
  const goalText = () => {
    if (!goalLines.length) return "";
    const last = goalLines[goalLines.length - 1], whole = goalLines.join(" ");
    if (/^[A-Z"]/.test(goalLines[0])) {
      if (goalMem[last] !== whole && goalLines.length > 1) { goalMem[last] = whole; try { localStorage.setItem("rotk-goals", JSON.stringify(goalMem)); } catch (e) {} }
      return whole;
    }
    return goalMem[last] || "";
  };
  setInterval(() => {
    try {
      const v = view(); if (!v) return;
      const st = v.H[v.iw + ST];
      if (st !== 16) { goalSt = st; return; }
      if (goalSt !== 16) { goalSt = 16; goalLines = []; goalT = performance.now(); }
      if (performance.now() - goalT > 1500 || goalLines.length >= 5) return;
      let s = ""; for (let i = 0; i < 64; i++) { const c = v.H[v.iw + GOAL + i]; if (!c) break; if (c < 32 || c > 126) { s = ""; break; } s += String.fromCharCode(c); }
      s = s.trim();
      if (s.length >= 2 && goalLines[goalLines.length - 1] !== s) goalLines.push(s);
    } catch (e) {}
  }, 3);
  let own = 0;   // our own presses skip the d-pad handling below
  const gi = (id, v) => { own++; try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} own--; };
  // online games send presses with the buttons a little later (same as the HD Backpack's press)
  const tap = (id) => new Promise((res) => { const d = window.__mp && window.__mp.sync ? 50 : 0; setTimeout(() => { gi(id, 1); setTimeout(() => { gi(id, 0); setTimeout(res, 140 + d); }, 90); }, d); });
  const view = () => {
    const M = window.__wideM; if (!M || !M.HEAPU8 || !M._rotk_iwram) return null;
    if (M._rotk_link_iwram && M._rotk_link_on && M._rotk_link_on() && window.__mp && window.__mp.online && !window.__mp.sync) return null;
    const onl = !!(window.__mp && window.__mp.online), me = onl ? window.__mp.me & 1 : 0;
    const iw = onl && M._rotk_link_iwram ? M._rotk_link_iwram(me) : M._rotk_iwram();
    const ew = onl && M._rotk_link_ewram ? M._rotk_link_ewram(me) : M._rotk_ewram ? M._rotk_ewram() : 0;
    return iw ? { H: M.HEAPU8, iw, ew } : null;
  };
  // ---- v220 (Jordan: "if it is a block menu you should be able to move an item in all four directions or move the
  // cursor in all 4 directions"; "bonus map selection still functions like the old menu") ----
  // The d-pad (pad, keyboard, joystick) goes through the emulator's simulateInput; on grid screens the page answers it:
  //   HD Backpack (state 10): the cursor moves to the box that is really up / down / left / right of it on screen
  //     (the game's own cursor graph doesn't match the HD layout). Browsing: the page's cursor request (EWRAM
  //     0x0203F603 = box + 1, then a Down press, as a tap does). Move Item: the game's target cursor is walked there.
  //   Choose Your Path (state 24): Up / Down move between rows of map cards, and to the difficulty row; A starts.
  const nearBox = (sel, from, id, ok) => {
    const cells = Array.from(document.querySelectorAll(sel)).filter((c) => !ok || ok(+c.dataset.c) || +c.dataset.c === from), f = cells.find((c) => c.dataset.c === String(from));
    if (!f) return null;
    const a = f.getBoundingClientRect(), ax = a.left + a.width / 2, ay = a.top + a.height / 2;
    let best = null, bd = 1e9;
    for (const c of cells) {
      if (c === f) continue;
      const b = c.getBoundingClientRect(), dx = b.left + b.width / 2 - ax, dy = b.top + b.height / 2 - ay;
      const along = id === 7 ? dx : id === 6 ? -dx : id === 5 ? dy : -dy, side = id >= 6 ? Math.abs(dy) : Math.abs(dx);
      if (along < Math.min(a.width, a.height) * 0.3 || side > along * 1.2) continue;   // only boxes inside a 50-degree cone that way
      const d = along + side * 2.5;
      if (d < bd) { bd = d; best = c; }
    }
    return best ? +best.dataset.c : null;
  };
  const held = {};
  let stashT = -1, lastStash = "";
  setInterval(() => {   // Move Item: show the stash box the d-pad picked as the cursor
    const bp = document.getElementById("hdBp"); if (!bp || bp.hidden) { stashT = -1; return; }
    const want = stashT >= 0 ? String(stashT) : "";
    bp.querySelectorAll(".cell.hdpick").forEach((c) => { if (c.dataset.c !== want) c.classList.remove("hdpick"); });
    if (!want) { bp.querySelectorAll(".cell.hdcur").forEach((c) => { c.classList.remove("hdcur"); c.classList.add("cur"); }); return; }
    const c = bp.querySelector('.cell[data-c="' + want + '"]'); if (c) c.classList.add("hdpick", "cur");
    bp.querySelectorAll(".cell.cur").forEach((o) => { if (o !== c) { o.classList.remove("cur"); o.classList.add("hdcur"); } });
  }, 30);   // a direction the page answered: its release is ours too
  let bm = { focus: 0, diff: 0, go: 0, t: 0 };   // Choose Your Path: which row the d-pad is on, the difficulty picked, starting
  const walkSeq = async (seq) => { busy = 1; try { for (const k of seq) await tap(k); } finally { busy = 0; } };
  const handle = (id, v) => {
    const vw = view(); if (!vw) return false;
    const { H, iw, ew } = vw, st = H[iw + ST], sub = H[iw + SUB];
    if (st === 24 && id === 0 && v) { bm.go = 0; return false; }
    if (st !== 10 || sub !== 6) stashT = -1;
    if (st === 10 && sub === 6 && id === 0 && v) { stashT = -1; return false; }
    if (st === 10 && sub === 6 && id === 8 && v && stashT >= 0 && ew) { H[ew + 0x3F604] = stashT - 30 + 1; stashT = -1; held[8] = 1; return true; }   // put it in that stash box (the game's Move Item swap)   // B: back out (the page stops answering the game's steps)
    if (id < 4 || id > 8) return false;
    if (!v) { if (held[id]) { delete held[id]; return true; } return false; }
    if (st === 10 && id !== 8 && ew && document.querySelector("#hdBp:not([hidden])")) {
      const curEl = document.querySelector("#hdBp .cell.cur"); if (!curEl) return false;
      const from = sub === 6 && stashT >= 0 ? stashT : +curEl.dataset.c;
      if (sub === 0) {
        const to = nearBox("#hdBp .cell[data-c]", from, id); held[id] = 1;
        if (to === null || busy) return true;
        H[ew + 0x3F603] = to + 1; walkSeq([5]);
        return true;
      }
      if (sub === 6) {   // Move Item: backpack boxes 8-14 and the stash box shown as box 15 (the game's 4 x 2 grid)
        // the stash box the game shows as its box 15 (EWRAM 0x0203F868 + player: which of the 5)
        const cellsSel = "#hdBp .iv .cell[data-c]", winBox = 30 + Math.min(4, H[ew + 0x3F868 + (H[iw + 0x3F59] & 1)]);
        const to = nearBox(cellsSel, from, id, (c) => (c >= 8 && c <= 14) || (c >= 30 && c < 35)); held[id] = 1;
        if (to === null || busy) return true;
        // the other stash boxes: the page holds the pick (gold) until A, then asks for the game's swap (EWRAM 0x0203F604)
        if (to >= 30 && to !== winBox) { stashT = to; lastStash = ""; return true; }
        stashT = -1;
        const g = (c) => (c >= 30 ? 15 : c);
        const real = document.querySelector("#hdBp .cell.hdcur") || curEl, a = g(+real.dataset.c), b = g(to); let x = a & 3, y = (a >> 2) & 1; const tx = b & 3, ty = (b >> 2) & 1, seq = [];
        while (x < tx) { seq.push(7); x++; } while (x > tx) { seq.push(6); x--; } while (y < ty) { seq.push(5); y++; } while (y > ty) { seq.push(4); y--; }
        if (seq.length) walkSeq(seq);
        return true;
      }
      return false;
    }
    if (st === 24 && sub === 0) {
      const tall = el && el.classList.contains("tall"), cur = H[iw + CUR] & 3, cols = tall ? 2 : 4;
      if (id === 8) { bm.go = 1; bm.t = performance.now(); return false; }   // A: the game opens the map; the page goes on
      held[id] = 1;
      if (busy) return true;
      if (bm.focus === 1) {
        if (id === 6 || id === 7) { bm.diff = Math.max(0, Math.min(2, bm.diff + (id === 7 ? 1 : -1))); lastKey = ""; }
        else if (id === 4) { bm.focus = 0; lastKey = ""; }
        return true;
      }
      if (id === 6 || id === 7) { held[id] = 0; delete held[id]; return false; }   // across: the game's own
      const row = (cur / cols) | 0, rows = Math.ceil(4 / cols);
      if (id === 5 && row === rows - 1) { bm.focus = 1; lastKey = ""; return true; }
      if (id === 4 && row === 0) return true;
      const to = cur + (id === 5 ? cols : -cols), seq = []; for (let k = cur; k !== to; k += to > cur ? 1 : -1) seq.push(to > cur ? 7 : 6);
      walkSeq(seq);
      return true;
    }
    return false;
  };
  setInterval(() => {
    const g = window.EJS_emulator && window.EJS_emulator.gameManager;
    if (!g || g.__hdGridWrap || typeof g.simulateInput !== "function") return;
    const orig = g.simulateInput;
    g.simulateInput = function (p, id, v) { if (!own && !window.__padOwn && !p) { let h = false; try { h = handle(id, v); } catch (e) {} if (h) return; } return orig.apply(this, arguments); };
    g.__hdGridWrap = true;
  }, 500);
  function build() {
    el = document.createElement("div"); el.id = "hdMenu"; el.hidden = true;
    el.innerHTML = '<style>' +
      '#hdMenu{position:fixed;z-index:22;overflow:hidden;box-sizing:border-box;color:#f6ead0;font:600 var(--fs)/1.2 var(--display,Georgia,serif);user-select:none;-webkit-user-select:none;touch-action:manipulation}' +
      '#hdMenu[hidden]{display:none}' +
      '#hdMenu canvas.bg{position:absolute;inset:0;width:100%;height:100%}' +
      '#hdMenu .ban{position:absolute;top:0;width:calc(var(--fs)*2.6);height:min(62%,calc(var(--fs)*10));background:linear-gradient(90deg,#101a33,#1d2c52 50%,#101a33);clip-path:polygon(0 0,100% 0,100% 88%,50% 100%,0 88%);box-shadow:inset 0 0 0 2px #c79a3e;display:flex;justify-content:center;padding-top:22%;box-sizing:border-box}' +
      '#hdMenu .ban::before{content:"";position:absolute;inset:3px 3px 6px;clip-path:inherit;border:1px solid rgba(232,190,100,0.6)}' +
      '#hdMenu .ban .tr{width:70%;height:auto;color:#e9c46f;filter:drop-shadow(0 0 4px rgba(255,200,100,0.6))}' +
      '#hdMenu .ban.l{left:calc(max(5%,var(--fs)*2.2))}#hdMenu .ban.r{right:calc(max(5%,var(--fs)*2.2))}' +
      '#hdMenu .mid{position:absolute;inset:calc(var(--top,0px) + 2%) calc(max(5%,var(--fs)*2.2) + var(--fs)*3) 3%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:calc(var(--fs)*0.42)}' +
      '#hdMenu .hd{font:700 min(calc(var(--fs)*1.9),calc(var(--mw)*0.13))/1.05 var(--display,Georgia,serif);letter-spacing:.03em;background:linear-gradient(#fff3c9,#e7b552 55%,#a8742a);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.8));text-align:center;white-space:nowrap}' +
      '#hdMenu .orn{width:76%;height:calc(var(--fs)*0.7);background:linear-gradient(90deg,transparent,#d9a94c 20%,#f6dc93 50%,#d9a94c 80%,transparent) center/100% 1.5px no-repeat;position:relative}' +
      '#hdMenu .orn::after{content:"";position:absolute;left:50%;top:50%;width:calc(var(--fs)*0.5);height:calc(var(--fs)*0.5);background:linear-gradient(135deg,#fff1c0,#c88d2e);transform:translate(-50%,-50%) rotate(45deg);box-shadow:0 0 6px rgba(255,200,90,0.8)}' +
      '#hdMenu .bar{position:relative;width:100%;max-width:calc(var(--fs)*17);height:calc(var(--fs)*1.85);flex:0 0 auto;display:flex;align-items:center;justify-content:center;cursor:pointer;' +
        'background:linear-gradient(#b98a3a,#5f4219 50%,#c99a46);clip-path:polygon(4.5% 0,95.5% 0,100% 50%,95.5% 100%,4.5% 100%,0 50%);transition:transform .12s,filter .12s}' +
      '#hdMenu .bar::before{content:"";position:absolute;inset:2px;clip-path:inherit;background:linear-gradient(#1c1a1f,#0d0c10 55%,#1f1c1a)}' +
      '#hdMenu .bar>*{position:relative}' +
      '#hdMenu .bar{display:grid;grid-template-columns:calc(var(--fs)*2.6) 1fr calc(var(--fs)*2.6);column-gap:calc(var(--fs)*0.4);justify-items:center}' +
      '#hdMenu .bar svg{width:calc(var(--fs)*1.05);height:calc(var(--fs)*1.05);justify-self:end;fill:none;stroke:#e6b95a;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}' +
      '#hdMenu .bar b{font-weight:600;font-size:calc(var(--fs)*0.92);letter-spacing:.02em;color:#efe4cc;text-shadow:0 1px 2px #000;white-space:nowrap}' +
      '#hdMenu .bar.sel{background:linear-gradient(#fff0b8,#d8a240 45%,#fff0b8);filter:drop-shadow(0 0 calc(var(--fs)*0.5) rgba(255,190,80,0.85));transform:scale(1.05)}' +
      '#hdMenu .bar.sel::before{background:linear-gradient(#3b2c14,#1a1209 55%,#3a2a12)}' +
      '#hdMenu .bar.sel b{color:#ffe9a8}#hdMenu .bar.sel svg{stroke:#ffd77a}' +
      '#hdMenu .goal{width:100%;max-width:calc(var(--fs)*22);margin-top:calc(var(--fs)*0.25);padding:calc(var(--fs)*0.55) calc(var(--fs)*0.9);box-sizing:border-box;color:#2b1d10;font:500 calc(var(--fs)*0.9)/1.3 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;text-align:left;' +
        'background:radial-gradient(ellipse at 30% 40%,#fbf1d4,#ecd9a8 60%,#d2b57a);border:2px solid #b8893a;box-shadow:0 0 0 1px #4a3415,inset 0 0 calc(var(--fs)*1.4) rgba(120,80,30,0.45),0 4px 12px rgba(0,0,0,0.6);border-radius:3px}' +
      '#hdMenu .goal[hidden]{display:none}' +
      '#hdMenu .bar.opt{max-width:calc(var(--fs)*24);grid-template-columns:calc(var(--fs)*2.2) 1fr auto;justify-items:start;padding-right:calc(var(--fs)*1.2);box-sizing:border-box}' +
      '#hdMenu .bar.opt svg{justify-self:center}' +
      '#hdMenu .val{display:flex;align-items:center;gap:calc(var(--fs)*0.35);color:#f3d27a;font-size:calc(var(--fs)*0.9)}' +
      '#hdMenu .val em{font-style:normal;min-width:calc(var(--fs)*3.6);text-align:center;font-weight:700;text-shadow:0 1px 2px #000}' +
      '#hdMenu .val u{text-decoration:none;font-size:calc(var(--fs)*1.3);line-height:.8;padding:0 calc(var(--fs)*0.25);color:#c99a46}' +
      '#hdMenu .bar.sel .val u{color:#ffe08a}' +
      '#hdMenu .pips{display:flex;gap:calc(var(--fs)*0.14)}' +
      '#hdMenu .pips i{width:calc(var(--fs)*0.42);height:calc(var(--fs)*0.85);border:1px solid #8a6a30;border-radius:1px;background:#1a1612;transform:skewX(-12deg)}' +
      '#hdMenu .pips i.on{background:linear-gradient(#ffeaa0,#d59a34);border-color:#ffe08a;box-shadow:0 0 calc(var(--fs)*0.3) rgba(255,190,80,0.6)}' +
      '#hdMenu .val em.n{min-width:calc(var(--fs)*1.8)}' +
      '#hdMenu .book{position:relative;width:100%;flex:1 1 auto;min-height:0;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:calc(var(--fs)*0.55) calc(var(--fs)*1.1);padding:calc(var(--fs)*0.7) calc(var(--fs)*0.8);box-sizing:border-box;' +
        'background:linear-gradient(90deg,#4a3420,#6b4c2c 48%,#2a1d10 50%,#6b4c2c 52%,#4a3420);border:2px solid #b8893a;border-radius:6px;box-shadow:0 0 0 1px #2a1d10,0 6px 18px rgba(0,0,0,0.7),inset 0 0 calc(var(--fs)*2) rgba(0,0,0,0.6)}' +
      '#hdMenu .card{position:relative;min-height:0;min-width:0;overflow:hidden;gap:calc(var(--ch)*0.04);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;cursor:pointer;padding:calc(var(--fs)*0.3);box-sizing:border-box;color:#2b1d10;' +
        'font:600 calc(var(--fs)*0.85)/1.15 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;font-style:italic;' +
        'background:radial-gradient(ellipse at 40% 40%,#fbf1d4,#ecd9a8 60%,#cfae72);border:2px solid #a87a32;border-radius:4px;box-shadow:inset 0 0 calc(var(--fs)*1.2) rgba(120,80,30,0.5),0 2px 6px rgba(0,0,0,0.6);transition:transform .12s,box-shadow .12s}' +
      '#hdMenu .card.sel{border-color:#ffe08a;transform:scale(1.03);box-shadow:inset 0 0 calc(var(--fs)*1.2) rgba(120,80,30,0.4),0 0 0 2px #f6c45a,0 0 calc(var(--fs)*1.1) rgba(255,190,80,0.9)}' +
      '#hdMenu .card .tx{position:relative;align-self:stretch;text-align:center;font-size:var(--t2);line-height:1.35}' +
      '#hdMenu .card .nm{display:inline-block;margin-bottom:.2em;font-family:var(--display,Georgia,serif);font-weight:700;font-style:normal;font-size:var(--t1);white-space:nowrap}' +
      '#hdMenu .card .lv{display:inline-block;margin-top:.2em;font-weight:700;font-size:var(--t3);white-space:nowrap}' +
      '#hdMenu .card.empty{color:#7a6448;font-style:normal}' +
      '#hdMenu .card .tr{position:absolute;right:4%;bottom:6%;height:55%;width:auto;max-width:40%;color:rgba(120,85,40,0.2)}' +
      '#hdMenu .act{display:flex;align-items:center;gap:calc(var(--fs)*0.5);flex:0 0 auto;padding:calc(var(--fs)*0.25) calc(var(--fs)*1.2);border:1.5px solid #c99a46;border-radius:999px;background:linear-gradient(#1c1a1f,#0d0c10);color:#f3d27a;font:700 calc(var(--fs)*0.95)/1 var(--display,Georgia,serif);cursor:pointer}' +
      '#hdMenu .act i{display:grid;place-items:center;width:calc(var(--fs)*1.25);height:calc(var(--fs)*1.25);border-radius:50%;background:radial-gradient(#fff,#c9c3b6);color:#222;font:700 calc(var(--fs)*0.7)/1 var(--ui,system-ui,sans-serif);font-style:normal}' +
      '#hdMenu .mid.slots{inset:calc(var(--top,0px) + var(--fs)*0.2) calc(max(5%,var(--fs)*2.2) + var(--fs)*3) calc(var(--fs)*0.4);justify-content:flex-start}' +
      '#hdMenu.tall .mid.slots{inset:calc(var(--top,0px) + var(--fs)*0.2) calc(max(5%,var(--fs)*2.2) + var(--fs)*0.4) calc(var(--fs)*0.4)}#hdMenu.tall.sl .ban{display:none}' +
      '#hdMenu.tall.sl .mid{left:calc(var(--fs)*1.1);right:calc(var(--fs)*1.1)}' +
      '#hdMenu .ask{display:flex;align-items:center;gap:calc(var(--fs)*0.7);flex:0 0 auto;padding:calc(var(--fs)*0.3) calc(var(--fs)*1);border:1.5px solid #c99a46;border-radius:999px;background:linear-gradient(#1c1a1f,#0d0c10);color:#f6ead0;font:600 calc(var(--fs)*0.9)/1.1 var(--display,Georgia,serif);white-space:nowrap}' +
      '#hdMenu.tall .ask{flex-wrap:wrap;justify-content:center;white-space:normal;text-align:center;border-radius:calc(var(--fs)*1);row-gap:calc(var(--fs)*0.4)}#hdMenu.tall .ask span{flex:0 0 100%}' +
      '#hdMenu .yn{padding:calc(var(--fs)*0.2) calc(var(--fs)*0.8);border:1.5px solid #8a6a30;border-radius:999px;color:#e6c27a;cursor:pointer;font-weight:700}' +
      '#hdMenu .yn.sel{border-color:#ffe08a;color:#2b1d10;background:linear-gradient(#fff0b8,#d8a240);box-shadow:0 0 calc(var(--fs)*0.6) rgba(255,190,80,0.8)}' +
      '#hdMenu .card .hp{display:inline-flex;align-items:center;gap:.3em;margin:.15em 0}#hdMenu .card .hp .nm{font-size:calc(var(--t1)*1.05);margin:0}#hdMenu .card .hp u{flex:0 0 auto}#hdMenu .card .hp u{text-decoration:none;font:700 calc(var(--t1)*1.1)/1 var(--display,Georgia,serif);color:#8a5a1a;cursor:pointer;padding:0 .25em}' +
      '#hdMenu .goal.q{text-align:center;max-width:calc(var(--fs)*18);font-size:calc(var(--fs)*1)}' +
      '#hdMenu .maps{display:grid;grid-template-columns:repeat(4,1fr);gap:calc(var(--fs)*0.6);width:100%;max-width:calc(var(--fs)*30)}' +
      '#hdMenu .mapc{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:calc(var(--fs)*0.2);padding:calc(var(--fs)*0.5) calc(var(--fs)*0.3);min-width:0;cursor:pointer;text-align:center;color:#2b1d10;' +
        'font:italic 500 calc(var(--fs)*0.75)/1.15 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;background:radial-gradient(ellipse at 40% 40%,#fbf1d4,#ecd9a8 60%,#cfae72);border:2px solid #a87a32;border-radius:4px;box-shadow:inset 0 0 calc(var(--fs)*1.2) rgba(120,80,30,0.5),0 2px 6px rgba(0,0,0,0.6);transition:transform .12s}' +
      '#hdMenu .mapc svg{width:calc(var(--fs)*2.4);height:calc(var(--fs)*2.4);fill:none;stroke:#6b4518;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}' +
      '#hdMenu .mapc .nm{font:700 calc(var(--fs)*0.85)/1.1 var(--display,Georgia,serif);font-style:normal}' +
      '#hdMenu .mapc.sel{border-color:#ffe08a;transform:scale(1.05);box-shadow:inset 0 0 calc(var(--fs)*1.2) rgba(120,80,30,0.4),0 0 0 2px #f6c45a,0 0 calc(var(--fs)*1.1) rgba(255,190,80,0.9)}' +
      '#hdMenu .goal.pth{display:grid;grid-template-columns:1fr 1fr;gap:calc(var(--fs)*1);max-width:calc(var(--fs)*30)}' +
      '#hdMenu .pth div{display:flex;flex-wrap:wrap;align-items:center;gap:calc(var(--fs)*0.35)}#hdMenu .pth i{flex:0 0 100%;font:700 calc(var(--fs)*0.85)/1.2 var(--display,Georgia,serif);color:#6b4518;font-style:normal}' +
      '#hdMenu .pk{padding:calc(var(--fs)*0.15) calc(var(--fs)*0.6);border:1.5px solid #a87a32;border-radius:999px;cursor:pointer;font-weight:600}' +
      '#hdMenu .pk.sel{background:linear-gradient(#3b2c14,#1a1209);color:#ffe08a;border-color:#ffe08a;box-shadow:0 0 calc(var(--fs)*0.5) rgba(255,190,80,0.8)}#hdMenu .pk.dim{opacity:.55}' +
      '#hdMenu .goal.pth.one{display:flex;flex-direction:column;align-items:center;gap:calc(var(--fs)*0.35);max-width:calc(var(--fs)*24)}#hdMenu .pth.one div{justify-content:center}#hdMenu .pth.one i{flex:none}' +
      '#hdMenu .pk.on{border-color:#6b4518;background:rgba(107,69,24,0.18);color:#3b2410;font-weight:700}' +
      '#hdMenu .mapc.on{border-color:#d8a240;box-shadow:inset 0 0 calc(var(--fs)*1.2) rgba(120,80,30,0.4),0 0 0 2px #b8893a}' +
      '#hdMenu .acts2{display:flex;gap:calc(var(--fs)*0.8)}#hdMenu .act.go{border-color:#ffe08a;background:linear-gradient(#3b2c14,#1a1209);box-shadow:0 0 calc(var(--fs)*0.6) rgba(255,190,80,0.6)}#hdMenu .act.busy{opacity:.7}' +
      '#hdMenu.tall .maps{grid-template-columns:repeat(2,1fr)}#hdMenu.tall .goal.pth{grid-template-columns:1fr}' +
      '#hdMenu .mid.slots .hd{font-size:min(calc(var(--fs)*1.5),calc(var(--mw)*0.11))}' +
            '</style><canvas class="bg"></canvas><div class="ban l">' + TREE + '</div><div class="ban r">' + TREE + '</div><div class="mid"></div>';
    // inside the game stage, under its own buttons (P2, Levels, Page 1 of 2 stay on top, z 28) and the touch pad (z 25)
    (document.getElementById("stage") || document.body).appendChild(el);
    bg = el.querySelector("canvas.bg");
    el.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); });
    el.addEventListener("click", async (e) => {
      const bd = e.target.closest("[data-bmd]");
      if (bd) { bm.diff = +bd.dataset.bmd; bm.focus = 1; lastKey = ""; return; }
      if (e.target.closest("[data-bmgo]")) { if (!busy && !bm.go) { bm.go = 1; bm.t = performance.now(); busy = 1; try { await tap(8); } finally { busy = 0; } } return; }
      if (e.target.closest("[data-bm]")) bm.focus = 0;
      const w = e.target.closest("[data-walk]");
      if (w) { if (!busy) { busy = 1; try { await walk(w.dataset); } finally { busy = 0; } } return; }
      if (e.target.closest(".back")) { if (!busy) { busy = 1; try { await tap(0); } finally { busy = 0; } } return; }
      const cd = e.target.closest(".card"), ac = e.target.closest(".act");
      if ((cd || ac) && !busy) { busy = 1; try { await slotTap(cd ? +cd.dataset.i : -1); } finally { busy = 0; } return; }
      const b = e.target.closest(".bar"); if (!b || busy) return;
      const v = view(); if (!v) return;
      const want = +b.dataset.i, st0 = v.H[v.iw + ST], m = MENUS[st0]; if (!m) return;
      const order = m.items.map((it, i) => it[2] === undefined ? i : it[2]), kind = (m.items[order.indexOf(want)] || [])[3];
      skipHold = performance.now() + 1500;
      const pip = e.target.closest("[data-v]"), arrow = e.target.closest("[data-d]");
      busy = 1;
      try {
        let there = false;
        for (let n = 0; n < 12; n++) {
          const now = view(); if (!now || now.H[now.iw + ST] !== st0) break;
          const cur = now.H[now.iw + CUR];
          if (cur === want) { there = true; break; }
          await tap(cur < want ? 5 : 4);
        }
        if (!there) return;
        if (!kind) { await tap(8); return; }
        // a setting: a volume pip walks the value there, an arrow steps it, the rest of the bar steps it forward
        const goal = pip ? +pip.dataset.v : null, dir = arrow ? +arrow.dataset.d : 1;
        for (let n = 0; n < (goal === null ? 1 : 12); n++) {
          const now = view(); if (!now || now.H[now.iw + ST] !== st0 || now.H[now.iw + CUR] !== want) break;
          const val = now.H[now.iw + OPT + want];
          if (goal !== null && val === goal) break;
          await tap((goal === null ? dir > 0 : goal > val) ? 7 : 6);
        }
      } finally { busy = 0; }
    });
  }
  // data-sub: get the game's sub-screen there first (A forward, B back); data-walk "addr,target,incKey,decKey":
  // step a cursor byte to target; data-press: then press that button
  async function walk(d) {
    const v0 = view(); if (!v0) return; const st0 = v0.H[v0.iw + ST];
    if (d.sub !== undefined) for (let n = 0; n < 4; n++) { const v = view(); if (!v || v.H[v.iw + ST] !== st0) return; const sb = v.H[v.iw + SUB]; if (sb === +d.sub) break; await tap(sb < +d.sub ? 8 : 0); await new Promise((r) => setTimeout(r, 150)); }
    if (d.walk) {
      const [a, t, inc, dec] = d.walk.split(",").map((x) => parseInt(x, 16));
      for (let n = 0; n < 12; n++) { const v = view(); if (!v || v.H[v.iw + ST] !== st0) return; const c = v.H[v.iw + a]; if (c === t) break; await tap(c < t ? inc : dec); }
    }
    if (d.press !== undefined) await tap(+d.press);
  }
  // a card: walk the slot cursor there (Left/Right across, Up/Down between rows), then A; the action bar is just A
  async function slotTap(want) {
    for (let n = 0; n < 6 && want >= 0; n++) {
      const v = view(); if (!v || v.H[v.iw + ST] !== 9) return;
      const cur = v.H[v.iw + 0x41BC] & 3;
      if (cur === want) break;
      if ((cur >> 1) !== (want >> 1)) await tap((want >> 1) > (cur >> 1) ? 5 : 4);
      else await tap((want & 1) > (cur & 1) ? 7 : 6);
    }
    await tap(8);
  }
  const slotHtml = (H, iw, cur, saving, sub) => {
    const q = H[iw + CUR];
    let cards = "";
    for (let k = 0; k < 4; k++) {
      const o = iw + 0x5630 + 0x70 * k;
      let used = false; for (let i = 0; i < 0x68; i++) { const b = H[o + i]; if (b !== 0 && b !== 0xff) { used = true; break; } }
      const hero = HERO[(H[o + 0x65] >> 4) & 7], lv = H[o + 0x5C] + 1, scr = H[o + 0x68];
      let place = ["", ""]; try { place = window.__lvName ? window.__lvName(scr) : place; } catch (e) {}
      const pick = sub === 4 && k === cur;   // a new game in this slot: the game asks for its hero (Left / Right)
      cards += '<div class="card' + (k === cur ? " sel" : "") + (used || pick ? "" : " empty") + '" data-i="' + k + '">' + TREE +
        (pick ? '<div class="tx"><span class="lv">New Game</span><br><span class="hp"><u data-walk="" data-press="6">\u2039</u><span class="nm" style="color:' + HERO[q & 7][1] + '">' + esc(HERO[q & 7][0]) + '</span><u data-walk="" data-press="7">\u203a</u></span><br>Choose your hero</div>' :
         used ? '<div class="tx"><span class="nm" style="color:' + hero[1] + '">' + esc(hero[0]) + "</span><br>" + esc([place[0], place[1]].filter(Boolean).join(" \u00b7 ")) + '<br><span class="lv">Level ' + lv + "</span></div>"
              : '<div class="tx"><span class="nm" style="color:#8a7050">Empty</span></div>') + "</div>";
    }
    const foot = sub === 1 ? '<div class="ask"><span>Overwrite this saved game?</span><b class="yn' + (q === 1 ? " sel" : "") + '" data-walk="41B8,1,6,7" data-press="8">Yes</b><b class="yn' + (q !== 1 ? " sel" : "") + '" data-walk="41B8,0,6,7" data-press="8">No</b></div>'
      : sub === 3 ? '<div class="ask"><span>Game saved successfully</span><b class="yn sel" data-walk="" data-press="8">OK</b></div>'
      : sub === 4 ? '<div class="act" data-walk="" data-press="8"><i>A</i>Start</div>'
      : '<div class="act"><i>A</i>' + (saving ? "Save" : "Load") + "</div>";
    return '<div class="orn"></div><div class="hd">' + (saving ? "Save Game" : H[iw + 0x41B4] === 4 ? "Bonus Maps" : "Load Game") + '</div><div class="book">' + cards + "</div>" + foot;
  };
  // a setting's value on the right of its bar: ‹ value ›, volumes as ten pips
  const optHtml = (kind, v) => {
    let mid;
    if (kind === "vol") { mid = '<span class="pips">'; for (let k = 1; k <= 10; k++) mid += '<i data-v="' + k + '"' + (k <= v ? ' class="on"' : "") + "></i>"; mid += '</span><em class="n">' + (v ? v : "Off") + "</em>"; }
    else mid = "<em>" + (kind === "on" ? (v ? "On" : "Off") : DIFF[v] || "?") + "</em>";
    return '<span class="val"><u data-d="-1">\u2039</u>' + mid + '<u data-d="1">\u203a</u></span>';
  };
  // Quit's question, Choose Your Path, and the GBA link's waiting screen
  const yn = (txt, q, yes) => '<div class="orn"></div><div class="hd">' + txt[0] + '</div><div class="orn"></div><div class="goal q">' + txt[1] + "</div>" +
    '<div class="bar' + (q === yes ? " sel" : "") + '" data-walk="41BC,' + yes + ',5,4" data-press="8"><svg viewBox="0 0 24 24">' + ICON.exit + "</svg><b>Yes</b><span></span></div>" +
    '<div class="bar' + (q !== yes ? " sel" : "") + '" data-walk="41BC,' + (1 - yes) + ',5,4" data-press="8"><svg viewBox="0 0 24 24">' + ICON.swords + "</svg><b>No</b><span></span></div>";
  // v220: one screen like the other new menus: tap a map, tap a difficulty, Start (or d-pad all four ways and A).
  // The game still asks map, level, difficulty one after another; the page answers its level and difficulty steps.
  const pathHtml = (H, iw, sub, cur) => {
    const going = bm.go || sub > 0;
    let cards = "";
    MAPS.forEach(([n, l, ic], k) => { cards += '<div class="mapc' + (k === cur && bm.focus === 0 ? " sel" : k === cur ? " on" : "") + '" data-walk="41B8,' + k + ',7,6" data-sub="0" data-bm="map"><svg viewBox="0 0 24 24">' + ICON[ic] + '</svg><span class="nm">' + esc(n) + "</span>" + (l ? "<em>" + esc(l) + "</em>" : "") + "</div>"; });
    const pills = ["Normal", "Hard", "Grueling"].map((t, k) => '<b class="pk' + (bm.diff === k ? (bm.focus === 1 ? " sel" : " on") : "") + '" data-bmd="' + k + '">' + esc(t) + "</b>").join("");
    return '<div class="orn"></div><div class="hd">Choose Your Path</div><div class="maps">' + cards + '</div><div class="goal pth one"><i>Difficulty</i><div>' + pills + "</div></div>" +
      '<div class="acts2"><div class="act back"><i>B</i>Back</div><div class="act go' + (going ? " busy" : "") + '" data-bmgo="1"><i>A</i>' + (going ? "Starting\u2026" : "Start") + "</div></div>";
  };
  const waitHtml = (t) => '<div class="orn"></div><div class="hd">Multiplayer</div><div class="orn"></div><div class="goal q">' + t + '</div><div class="act back"><i>B</i>Cancel</div>';
  const tick = () => {
    const hide = () => { if (el && !el.hidden) { el.hidden = true; lastKey = ""; } window.__hdMenuOn = false; };
    try {
      const v = view(); if (!v || window.__hdMenuOff) return hide();   // __hdMenuOff: tests compare with the game's own screen
      const { H, iw } = v, st = H[iw + ST], m = MENUS[st], sub = H[iw + SUB];
      if (!m || !MENU_SUB[st].includes(sub)) {
        // between two menu screens the game passes through a few frames of other states: keep the picture up for those
        if (st !== 1 && el && !el.hidden && performance.now() - lastOn < 700) return;
        return hide();
      }
      lastOn = performance.now();
      // GCN Link is gone from the title menu: if the cursor lands on it (keys, pads), step past it the same way
      if (st === 5 && sub !== 3 && H[iw + CUR] === 4 && !busy && performance.now() > skipHold) { busy = 1; tap(lastCur === 5 ? 4 : 5).finally(() => { busy = 0; }); }
      if (st === 5) lastCur = H[iw + CUR];
      // Choose Your Path: after A on a map the game asks its level (one per map) and then the difficulty: answer them
      if (st !== 24) bm = { focus: 0, diff: bm.diff, go: 0, t: 0 };
      else if (sub === 0 && bm.go && performance.now() - bm.t > 2500) bm.go = 0;   // backed out
      else if (!busy && sub > 0 && !bm.go) { busy = 1; tap(0).finally(() => { busy = 0; }); }   // backed out of a step: back to the maps
      else if (!busy && sub === 1) { bm.t = performance.now(); busy = 1; tap(8).finally(() => { busy = 0; }); }
      else if (!busy && sub === 2 && bm.go) { busy = 1; walk({ walk: "41B4," + bm.diff + ",5,4", press: "8" }).finally(() => { busy = 0; }); }
      const cv = document.getElementById("mpCanvas"); if (!cv) return hide();
      const r = cv.getBoundingClientRect(); if (!r.width || !r.height) return hide();
      if (!el) build();
      const cur = H[iw + CUR];
      const goal = m.goal ? goalText() : "";
      const saving = st === 9 && (H[iw + 0x41B4] === 1 || H[iw + 0x41B4] === 3), slotKey = st === 9 ? Array.from(H.subarray(iw + 0x5630, iw + 0x5630 + 0x1C0)).join(",") + "|" + H[iw + 0x41BC] + "|" + saving : "";
      // the stage's own buttons (P2 / Levels on the pause menu, Page 1 of 2 on the save slots) keep a strip at the top
      const top = (st === 16 || st === 9) ? 48 : 0, tall = r.height > r.width * 0.9;
      const fs = Math.max(9, Math.min((r.height - top) / (m.goal ? 17.5 : st === 6 ? 20.5 : st === 24 ? (tall ? 29 : 20.5) : 15.5), r.width / (st === 24 ? (tall ? 20 : 30) : st !== 6 ? 22 : tall ? 21 : 28)));
      const optKey = st === 6 ? Array.from(H.subarray(iw + OPT, iw + OPT + 7)).join(",") : "";
      const key = [st, cur, sub + "/" + bm.focus + bm.diff + bm.go + "/" + H[iw + 0x41B4] + "/" + H[iw + 0x41BC] + "/" + goal + slotKey + optKey + top, r.left, r.top, r.width, r.height].join("|");
      window.__hdMenuOn = true;
      if (key === lastKey && !el.hidden) return;
      const sizeChanged = !lastKey || lastKey.split("|").slice(3).join() !== key.split("|").slice(3).join();
      lastKey = key;
      el.style.left = r.left + "px"; el.style.top = r.top + "px"; el.style.width = r.width + "px"; el.style.height = r.height + "px";
      el.style.setProperty("--fs", fs.toFixed(1) + "px"); el.style.setProperty("--top", top + "px");
      el.style.setProperty("--mw", Math.max(1, r.width - 2 * (Math.max(0.05 * r.width, fs * 2.2) + fs * 3)).toFixed(0) + "px");
      if (sizeChanged || el.hidden) {
        const d = Math.min(2, window.devicePixelRatio || 1), W = Math.round(r.width * d), Hh = Math.round(r.height * d);
        if (bg.width !== W || bg.height !== Hh) { bg.width = W; bg.height = Hh; paint(bg); }
      }
      const mid = el.querySelector(".mid");
      mid.classList.toggle("slots", st === 9); mid.classList.toggle("path", st === 24);
      el.classList.toggle("sl", st === 9 || st === 6 || st === 24); el.classList.toggle("tall", tall);   // tall: phone held upright, the cards take the banners' room
      if (st === 9) {
        mid.innerHTML = slotHtml(H, iw, H[iw + 0x41BC] & 3, saving, sub);
        const c0 = mid.querySelector(".card"), cr = c0 && c0.getBoundingClientRect();   // card text follows the card's size
        if (cr && cr.height) {
          const ch = cr.height, cw = cr.width, bk = mid.querySelector(".book");
          bk.style.setProperty("--ch", ch.toFixed(0) + "px");
          bk.style.setProperty("--t1", Math.min(ch * 0.19, cw * 0.15, fs * 1.3).toFixed(1) + "px");
          bk.style.setProperty("--t2", Math.min(ch * 0.12, cw * 0.11, fs * 0.95).toFixed(1) + "px");
          bk.style.setProperty("--t3", Math.min(ch * 0.145, cw * 0.13, fs * 1.05).toFixed(1) + "px");
        }
      }
      else if (st === 16 && sub === 1) mid.innerHTML = yn(["Quit Game", "Are you sure you wish to quit?"], H[iw + 0x41BC], QUIT_YES);
      else if (st === 24) mid.innerHTML = pathHtml(H, iw, sub, cur);
      else if (st === 23 || (st === 5 && sub === 3)) mid.innerHTML = waitHtml(st === 23 ? "This link isn't used here." : "Waiting for the other player\u2026");
      else mid.innerHTML = (m.head ? '<div class="orn"></div><div class="hd">' + esc(m.head) + '</div><div class="orn"></div>' : '<div class="orn"></div>') +
        m.items.map(([t, ic, c, kind], i) => { c = c === undefined ? i : c;
          return '<div class="bar' + (kind || st === 6 ? " opt" : "") + (c === cur ? " sel" : "") + '" data-i="' + c + '"><svg viewBox="0 0 24 24">' + ICON[ic] + "</svg><b>" + esc(t) + "</b>" + (kind ? optHtml(kind, H[iw + OPT + c]) : "<span></span>") + "</div>"; }).join("") +
        (m.head ? "" : '<div class="orn"></div>') + (st === 6 ? '<div class="act back"><i>B</i>Back</div>' : "") +
        (m.goal && goal ? '<div class="goal">' + esc(goal) + "</div>" : "");
      if (el.hidden) { el.hidden = false; shownAt = performance.now(); }
    } catch (e) { hide(); (window.__wideLog || (window.__wideLog = [])).push("hdMenu: " + (e && e.message || e)); }
  };
  setInterval(tick, 30);
  // the touch controls: Start glows gold like the menu bars (Jordan's example pictures)
  const css = document.createElement("style");
  css.textContent = "#pad .b-st{background:linear-gradient(180deg,#7a5418 0%,#3d2a0d 52%,#6e4c17 100%);border-color:#f6dc94;color:#ffe6a0;" +
    "box-shadow:0 0 0 3px #0d0b09,0 0 0 4.5px rgba(246,220,148,0.9),0 0 24px rgba(255,190,90,0.7),inset 0 1px 0 rgba(255,240,200,0.45),inset 0 -8px 14px rgba(0,0,0,0.45)}";
  document.head.appendChild(css);
})();
