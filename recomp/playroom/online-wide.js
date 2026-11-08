// Play Room v113: online 2-player in the Wide engine (lockstep, buttons only). Cut from the page.
  // Online in Wide (Jordan, 2026-11-08): the same lockstep as the Classic link below (each page runs both games and
  // only buttons travel), with the 2-player Wide engine in online mode (ROTK_LINK_NET: a frame runs only when the
  // page hands it both players' buttons; ROTK_LINK_SHOW: this player's game is the one shown and heard).
  // Returns false (nothing started) if the engine can't load, so the Classic link can take over.
  async function startLinkedWide(mp, game) {
    const s = mp.session, me = s.me, other = 1 - me, room = s.room;
    const say = (t) => { $("mpBanner").textContent = t; $("mpBanner").hidden = !t; };
    say("Loading the wide-view engine…");
    const unb64 = (t) => Uint8Array.from(atob(t), (c) => c.charCodeAt(0));
    const rom = game.slice();
    const at = (o, hex) => hex.match(/../g).every((b, i) => rom[o + i] === parseInt(b, 16));
    if (rom[0x2F88] === 0x80 && at(0x2F90, "281c403000283edbff2d3cdc")) { rom[0x2F88] = 0x84; rom.set([0x28, 0x1c, 0x40, 0x30, 0x80, 0x09, 0x06, 0x28, 0x3d, 0xd8, 0xc0, 0x46], 0x2F90); }
    let M;
    const log = (window.__wideLog = []);
    try {
      const sha = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-1", rom)), (x) => x.toString(16).padStart(2, "0")).join("");
      const V = "?v=113";
      const fetchBin = async (u) => { const r = await fetch(u); if (!r.ok) throw new Error(u + " " + r.status); return new Uint8Array(await r.arrayBuffer()); };
      if (!window.createRotkLink) await new Promise((res, rej) => { const sc = document.createElement("script"); sc.src = "wide/rotk-link.js" + V; sc.onload = res; sc.onerror = rej; document.body.appendChild(sc); });
      const [w0, w1, toml, bios] = await Promise.all([fetchBin("wide/rotk-link-0.wasm" + V), fetchBin("wide/rotk-link-1.wasm" + V), fetch("wide/game-link.txt").then((r) => r.text()), fetch("wide/bios.txt").then((r) => r.text()).then((t) => unb64(t.trim()))]);
      const wasm = new Uint8Array(w0.length + w1.length); wasm.set(w0); wasm.set(w1, w0.length);
      M = await window.createRotkLink({ wasmBinary: wasm, noInitialRun: true,
        preRun: [(mm) => Object.assign(mm.ENV, { ROTK_LINK: "1", ROTK_LINK_NET: "1", ROTK_LINK_SHOW: String(me), ROTK_LINK_ROM: "/data/game.gba", ROTK_LINK_BIOS: "/data/bios.bin", ROTK_LINK_SAVE0: "/data/saves/p0.sav", ROTK_LINK_SAVE1: "/data/saves/p1.sav", ROTK_LINK_VW: "240" })],
        print: (t) => { log.push(t); if (log.length > 200) log.shift(); }, printErr: (t) => { log.push(t); if (log.length > 200) log.shift(); } });
      if (typeof M._rotk_link_push !== "function") throw new Error("old engine");
      M.FS.mkdir("/data"); M.FS.mkdir("/data/saves");
      M.FS.writeFile("/data/game.gba", rom); M.FS.writeFile("/data/bios.bin", bios);
      M.FS.writeFile("/data/game.toml", toml.split("dd6d504c587ce487c983968f4f01748457b30ed8").join(sha).replace(/^view_width = \d+$/m, "view_width = 240"));
      s.savBytes.forEach((b, i) => { if (b && b.length) M.FS.writeFile("/data/saves/p" + i + ".sav", b); });
      M.FS.chdir("/data");
    } catch (e) { log.push("online wide: " + e); return false; }

    const H = WideHost;
    H.keepAspect = true;
    document.body.classList.add("wide-view");
    const cv = document.createElement("canvas"); cv.width = 960; cv.height = 720; cv.id = "mpCanvas"; $("game").appendChild(cv);
    H.canvas = cv; H.nativeView = () => M._rotk_native_view();
    let gl = null; try { gl = cv.getContext("webgl2", { alpha: false, antialias: false, depth: false, stencil: false }); } catch (e) {}
    H.sharp = gl ? makeSharpHD(gl) : null;
    const refit = () => { H.fitDue = true; }; window.addEventListener("resize", refit); window.addEventListener("orientationchange", refit);
    try { new ResizeObserver(refit).observe($("game")); } catch (e) {}
    if (H.sharp) cv.style.imageRendering = "auto";
    else { if (gl) { const c2 = document.createElement("canvas"); c2.width = 960; c2.height = 720; c2.id = "mpCanvas"; cv.replaceWith(c2); H.canvas = c2; } H.ctx = H.canvas.getContext("2d"); }
    const ac = window.__preAudio || null;
    if (ac) {
      try {
        const lp = ac.createBiquadFilter(), gain = ac.createGain();
        lp.type = "lowpass"; lp.frequency.value = 7200; gain.gain.value = 1.1; lp.connect(gain); gain.connect(ac.destination);
        H.audio = ac; H.out = lp; H.gain = gain; ac.resume().catch(() => {});
      } catch (e) {}
    }

    let held = 0, qsWant = false, frame = 0, sent = -1;
    const mine = new Map(), theirs = new Map(), myHash = new Map(); let theirHash = null, peerSeen = false, gone = false;
    const saveBuf = M._malloc(512);
    const readSave = () => { try { if (M._rotk_link_save(me, saveBuf) < 0) return null; return M.HEAPU8.slice(saveBuf, saveBuf + 512); } catch (e) { return null; } };
    const fake = {
      started: true,
      Module: { get HEAPU8() { return M.HEAPU8; }, AL: null },
      gameManager: {
        simulateInput: (p, id, v) => { const b = LIBRETRO_TO_GBA[id]; if (!b) return; held = v ? (held | b) : (held & ~b); },
        getFrameNum: () => frame,
        saveSaveFiles: () => {},
        getSaveFile: readSave,
        getSaveFilePath: () => "", loadSaveFiles: () => {}, restart: () => {}, setVariable: () => {},
        toggleFastForward: () => {}, setFastForwardRatio: () => {},
        mpQs: () => { qsWant = true; },
      },
      changeSettingOption: () => {}, enableShader: () => {}, play: () => { try { ac && ac.resume(); } catch (e) {} },
    };
    window.__mp = { iwram: () => M._rotk_link_iwram(me), ewram: () => M._rotk_link_ewram(me), frame: () => frame, M, me, online: true, hashes: () => myHash, net: () => ({ rtt: Math.round(rtt), delay }) };
    window.__wideM = M;
    window.EJS_emulator = fake;
    try { M._rotk_main(); } catch (e) { if (e !== "unwind" && !(e && e.name === "ExitStatus")) { log.push("online start: " + e); say("The 2-player game didn't start. Reload the page and link up again."); return true; } }
    const draw = () => { H.draw(); requestAnimationFrame(draw); };
    requestAnimationFrame(draw);
    try { window.EJS_onGameStart(); } catch (e) {}
    const KEYS = { ArrowUp: 4, ArrowDown: 5, ArrowLeft: 6, ArrowRight: 7, z: 8, x: 0, Enter: 3, v: 2, q: 10, e: 11 };
    const key = (e, v) => {
      let id = KEYS[e.key.length === 1 ? e.key.toLowerCase() : e.key]; if (id === undefined) return; e.preventDefault();
      if (id === 0 || id === 8 || id === 10 || id === 11) { const b = document.querySelector('#pad .btn[data-in="' + id + '"]'); if (b && b.__press) { if (!e.repeat) b.__press(v); return; } }
      fake.gameManager.simulateInput(0, id, v);
    };
    window.addEventListener("keydown", (e) => key(e, 1)); window.addEventListener("keyup", (e) => key(e, 0));
    let lastCloud = window.__cloudSaved || 0;
    setInterval(() => { if ((window.__cloudSaved || 0) !== lastCloud) { lastCloud = window.__cloudSaved; try { localStorage.setItem("rotk-mp-newer", s.mod); } catch (e) {} } }, 1000);

    const applyQs = (k, p) => { if (!(k & QS_BIT)) return; const b = M._rotk_link_iwram(p), h = M.HEAPU8; h[b + 0x5820] |= 8; h[b + 0x3D9A] |= 2; h[b + 0x3F46] |= 2; };
    const theirRole = me ? "h" : "g";
    let lastPub = 0, hs = null, echo = null, pingId = 0, pingAt = 0, lastPing = 0, rtt = 0, delay = MP.delay;
    room.onPeers(() => {
      const p = room.peers().find((q) => !q.sameTab && q.presence && q.presence.role === theirRole);
      if (!p) { if (peerSeen && !gone) { gone = true; say("Your friend left the game."); } return; }
      peerSeen = true;
      const pr = p.presence;
      if (typeof pr.f === "number" && Array.isArray(pr.k)) {
        const from = pr.f - pr.k.length + 1;
        for (let i = 0; i < pr.k.length; i++) if (from + i >= frame && !theirs.has(from + i)) theirs.set(from + i, pr.k[i] | 0);
      }
      if (pr.hs && typeof pr.hs.f === "number") theirHash = pr.hs;
      if (typeof pr.pi === "number") echo = pr.pi;
      if (typeof pr.po === "number" && pr.po === pingId && pingAt) { const r = performance.now() - pingAt; rtt = rtt ? rtt * 0.7 + r * 0.3 : r; pingAt = 0; }
    });
    const publish = (now) => {
      if (now - lastPub < 30) return; lastPub = now;
      if (!pingAt && now - lastPing > 500) { pingId++; pingAt = now; lastPing = now; }
      else if (pingAt && now - pingAt > 3000) pingAt = 0;
      if (rtt) delay = Math.max(4, Math.min(24, Math.round(rtt / 2 / 16.74) + 3));
      const from = Math.max(0, sent - MP.keep + 1), k = [];
      for (let f = from; f <= sent; f++) k.push(mine.get(f) | 0);
      room.presence({ f: sent, k, hs, pi: pingId, po: echo }).catch(() => {});
    };
    const step = 1000 / 59.7275; let acc = 0, last = performance.now(), waitSince = 0;
    say(""); $("bootCover").classList.add("gone");
    const tick = (now) => {
      acc += Math.min(100, now - last); last = now;
      while (sent < frame + delay) { sent++; let k = held; if (qsWant) { k |= QS_BIT; qsWant = false; } mine.set(sent, k); }
      publish(now);
      let ran = 0;
      // Frames are handed to the engine, which runs them on its next picture (a few at most at once).
      while (acc >= step && ran < 4 && !hashAt && M._rotk_link_queued() < 6) {
        const a = mine.get(frame), b = theirs.get(frame);
        if (a === undefined || b === undefined) { acc = Math.min(acc, step); break; }
        const k0 = me === 0 ? a : b, k1 = me === 0 ? b : a;
        if (M._rotk_link_queued() > 0 && ((k0 | k1) & QS_BIT)) break;   // memory changes wait until the queue is empty
        applyQs(k0, 0); applyQs(k1, 1);
        M._rotk_link_push(k0 & 0x3ff, k1 & 0x3ff);
        mine.delete(frame - 300); theirs.delete(frame - 300);
        frame++; acc -= step; ran++;
        if (frame % 120 === 0) hashAt = frame;
      }
      // Hash once the engine has actually run up to that frame.
      if (hashAt && M._rotk_link_queued() === 0) { const h = M._rotk_link_hash() >>> 0; myHash.set(hashAt, h); myHash.delete(hashAt - 1200); hs = { f: hashAt, h }; hashAt = 0; }
      if (ran) { waitSince = 0; if (!gone && $("mpBanner").textContent.startsWith("Waiting")) say(""); }
      else if (!gone) { if (!waitSince) waitSince = now; else if (now - waitSince > 1500) say("Waiting for your friend…"); }
      if (theirHash && myHash.has(theirHash.f)) { if (myHash.get(theirHash.f) !== theirHash.h && !gone) say("Your games fell out of step. Both of you reload the page and link up again."); theirHash = null; }
      requestAnimationFrame(tick);
    };
    let hashAt = 0;
    requestAnimationFrame(tick);
    return true;
  }

