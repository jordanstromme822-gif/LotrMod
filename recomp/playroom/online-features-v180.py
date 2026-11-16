#!/usr/bin/env python3
"""Play Room v180 (Jordan, 2026-11-16: "I'd like all updates to affect online and offline as well as multiplayer").

  online-features-v180.py in.html out.html

Online games (each page runs both games, only buttons travel) now get the v170-v179 features too. The engine (v180,
recomp/link/link_main.cpp) takes the page's own writes back out of the games before each picture and hands them to the
page (rotk_link_outbox); the page sends them with its next frame's buttons, and both pages write them right before that
frame runs (rotk_link_op). So any page feature that writes game memory stays in step without its own net code.

Turned on in online games: free 360 joystick + 16 facings (each player's own stick, mailbox [4 * player]), the hero
hook on both heroes, turning/chasing enemies (the host's chase setting), the HD Backpack (each player's own game),
Frodo's crossbow pickup and Bolt Trap wait, the extra skill buttons. Quick Skill Select (QS_BIT) is an op too now.
"""
import sys
src, dst = sys.argv[1:3]
s = open(src).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a)); s = s.replace(a, b)

# one engine build for every game
rep('const V = isLink ? "?v=179" : "?v=hd2";', 'const V = isLink ? "?v=180" : "?v=hd2";')
rep('      const V = "?v=172";\n', '      const V = "?v=180";   // v180: page writes travel with the buttons (rotk_link_op / outbox)\n')

# ---- online: page writes travel with the buttons (only inside startLinkedWide; the Classic link below looks alike) ----
W0 = s.index("async function startLinkedWide("); W1 = s.index("async function startLinked(", W0 + 10)
full, s = s, s[W0:W1]
rep("""    let held = 0, qsWant = false, frame = 0, sent = -1;
    const mine = new Map(), theirs = new Map(), myHash = new Map(); let theirHash = null, peerSeen = false, gone = false;""",
"""    let held = 0, qsWant = false, frame = 0, sent = -1;
    const mine = new Map(), theirs = new Map(), myHash = new Map(); let theirHash = null, peerSeen = false, gone = false;
    // v180: this page's writes to game memory (taken back out by the engine) go with the next frame's buttons as
    // [games, address, byte] triples; both pages write them right before that frame (host's first, then guest's).
    const netOn = typeof M._rotk_link_op === "function" && typeof M._rotk_link_outbox === "function";
    const myOps = new Map(), theirOps = new Map(); let opsWait = [];
    const outBuf = netOn ? M._malloc(8 * 512) : 0;
    const drainOut = () => {
      if (!netOn) return;
      for (let g = 0; g < 8; g++) {
        const n = M._rotk_link_outbox(outBuf, 512); if (n <= 0) break;
        const h = M.HEAPU8, dv = new DataView(h.buffer);
        for (let i = 0; i < n; i++) { const o = outBuf + 8 * i; opsWait.push(h[o + 5], dv.getUint32(o, true), h[o + 4]); }
        if (n < 512) break;
      }
    };
    const runOps = (ops) => { if (ops) for (let i = 0; i + 2 < ops.length; i += 3) M._rotk_link_op(ops[i] & 3, ops[i + 1] >>> 0, ops[i + 2] & 255, 0); };""")
# __mirrorIw: a page change to this player's game goes into the other game too (as in a P2 game)
rep("""    window.__wideM = M;
    window.EJS_emulator = fake;
    if (s.level) try { M._rotk_link_level(s.level); } catch (e) {}""",
"""    window.__wideM = M;
    window.EJS_emulator = fake;
    if (netOn) window.__mirrorIw = (off) => { const H8 = M.HEAPU8; H8[M._rotk_link_iwram(other) + off] = H8[M._rotk_link_iwram(me) + off]; };
    if (s.level) try { M._rotk_link_level(s.level); } catch (e) {}""")
# Quick Skill Select: an op (or) instead of a direct write
rep("""    const applyQs = (k, p) => { if (!(k & QS_BIT)) return; const b = M._rotk_link_iwram(p), h = M.HEAPU8; h[b + 0x5820] |= 8; h[b + 0x3D9A] |= 2; h[b + 0x3F46] |= 2; };""",
"""    const applyQs = (k, p) => {
      if (!(k & QS_BIT)) return;
      if (netOn) { M._rotk_link_op(1 << p, 0x03005820, 8, 1); M._rotk_link_op(1 << p, 0x03003D9A, 2, 1); M._rotk_link_op(1 << p, 0x03003F46, 2, 1); return; }
      const b = M._rotk_link_iwram(p), h = M.HEAPU8; h[b + 0x5820] |= 8; h[b + 0x3D9A] |= 2; h[b + 0x3F46] |= 2;
    };""")
rep("""      if (typeof pr.f === "number" && Array.isArray(pr.k)) {
        const from = pr.f - pr.k.length + 1;""",
"""      if (pr.o && typeof pr.o === "object") for (const f in pr.o) { const n = +f; if (n >= frame && !theirOps.has(n) && Array.isArray(pr.o[f])) theirOps.set(n, pr.o[f]); }
      if (typeof pr.f === "number" && Array.isArray(pr.k)) {
        const from = pr.f - pr.k.length + 1;""")
rep("""      for (let f = from; f <= sent; f++) k.push(mine.get(f) | 0);
      room.presence({ f: sent, k, hs, pi: pingId, po: echo }).catch(() => {});""",
"""      for (let f = from; f <= sent; f++) k.push(mine.get(f) | 0);
      const o = {}; let no = 0; for (let f = from; f <= sent; f++) { const x = myOps.get(f); if (x) { o[f] = x; no++; } }
      room.presence(no ? { f: sent, k, hs, pi: pingId, po: echo, o } : { f: sent, k, hs, pi: pingId, po: echo, o: null }).catch(() => {});""")
rep("""      while (sent < frame + delay) { sent++; let k = held; if (qsWant) { k |= QS_BIT; qsWant = false; } mine.set(sent, k); }""",
"""      drainOut();
      while (sent < frame + delay) {
        sent++; let k = held; if (qsWant) { k |= QS_BIT; qsWant = false; } mine.set(sent, k);
        if (opsWait.length) { myOps.set(sent, opsWait.slice(0, 3 * 400)); opsWait = opsWait.slice(3 * 400); }
      }""")
rep("""        if (M._rotk_link_queued() > 0 && ((k0 | k1) & QS_BIT)) break;   // memory changes wait until the queue is empty
        applyQs(k0, 0); applyQs(k1, 1);
        M._rotk_link_push(k0 & 0x3ff, k1 & 0x3ff);
        mine.delete(frame - 300); theirs.delete(frame - 300);""",
"""        if (!netOn && M._rotk_link_queued() > 0 && ((k0 | k1) & QS_BIT)) break;   // memory changes wait until the queue is empty
        if (netOn) { runOps(me === 0 ? myOps.get(frame) : theirOps.get(frame)); runOps(me === 0 ? theirOps.get(frame) : myOps.get(frame)); }
        applyQs(k0, 0); applyQs(k1, 1);
        M._rotk_link_push(k0 & 0x3ff, k1 & 0x3ff);
        mine.delete(frame - 300); theirs.delete(frame - 300); myOps.delete(frame - 300); theirOps.delete(frame - 300);""")
rep("""    window.__mp = { iwram: () => M._rotk_link_iwram(me), ewram: () => M._rotk_link_ewram(me), frame: () => frame, M, me, online: true, hashes: () => myHash, net: () => ({ rtt: Math.round(rtt), delay }) };""",
"""    window.__mp = { iwram: () => M._rotk_link_iwram(me), ewram: () => M._rotk_link_ewram(me), frame: () => frame, M, me, online: true, sync: netOn, hashes: () => myHash, net: () => ({ rtt: Math.round(rtt), delay }) };""")

wide, s = s, full[:W0]
s = s + wide + full[W1:]

# ---- the features ----
ONL = "(window.__mp && window.__mp.online && !window.__mp.sync)"   # an online game on an engine without op sync
# Frodo's crossbow pickup + Bolt Trap wait
rep("if (iwram < 0 || inMenu() || (window.__mp && window.__mp.online)) return false;", "if (iwram < 0 || inMenu() || %s) return false;" % ONL)
rep("if (iwram < 0 || (window.__mp && window.__mp.online)) return;", "if (iwram < 0 || %s) return;" % ONL)
# extra skill buttons
rep("""      const linked = () => !!(window.__mp && !window.__mp.wide);""",
"""      const linked = () => !!(window.__mp && !window.__mp.wide);
      const xLinked = () => linked() && !(window.__mp && window.__mp.sync);   // v180: online games have them too""")
rep("if (iwram >= 0 && h && !inMenu() && !linked()) {", "if (iwram >= 0 && h && !inMenu() && !xLinked()) {")
rep("const v = xList[k]; if (!v || xCast || inMenu() || linked()) return;", "const v = xList[k]; if (!v || xCast || inMenu() || xLinked()) return;")
# online: the skill goes back to R a bit later (the change reaches the game a few frames after it is made)
rep("""          xCast = null; updateExtras.key = null; updateExtras();
        }, 420);""",
"""          xCast = null; updateExtras.key = null; updateExtras();
        }, 420 + (window.__mp && window.__mp.sync && window.__mp.net ? (window.__mp.net().delay + 6) * 17 : 0));""")
# free 360 + hooks + enemies
rep('const freeM = () => { const M = window.__wideM; return M && window.__turn16 && typeof M._rotk_ewram === "function" && !(M._rotk_link_on && (!M._rotk_link_on() || (window.__mp && window.__mp.online))) ? M : null; };',
    'const freeM = () => { const M = window.__wideM; return M && window.__turn16 && typeof M._rotk_ewram === "function" && !(M._rotk_link_on && (!M._rotk_link_on() || %s)) ? M : null; };\n'
    '  const freeNet = () => !!(window.__mp && window.__mp.online);   // v180: online, each page writes its own player\'s mailbox; the engine sends it on' % ONL)
rep("""      if (!M._rotk_link_on) { const e = M._rotk_ewram() + FREE_MB; H[e] = fa; if (held) H[e + 1] = a; return; }""",
"""      if (!M._rotk_link_on) { const e = M._rotk_ewram() + FREE_MB; H[e] = fa; if (held) H[e + 1] = a; return; }
      if (freeNet()) { const p = window.__mp.me & 1; for (const [, ew] of freeGames(M)) { const e = ew + FREE_MB + 4 * p; H[e] = fa; if (held) H[e + 1] = a; } return; }""")
rep("""      for (const [iw, ew] of freeGames(M)) {
      if (H[iw + 0x41B0] !== 1) continue;                            // gameplay only
      const hero = dv.getUint32(iw + 0x3C00, true);
      if (hero < 0x02000000 || hero >= 0x02040000) continue;
      const at = ew + (hero - 0x02000000) + 0x14, cur = dv.getUint32(at, true);
      if (cur === FREE_GAME) dv.setUint32(at, FREE_HOOK, true);   // always on: it also turns Frodo's crossbows (16 facings)
      if (!freeOn()) H[ew + FREE_MB] = 0;                          // joystick 8 ways: the hook leaves his walk alone
      H[ew + FREE_MB + 3] = enemyChase() ? 1 : 0;                  // v177: chasing enemies walk straight at the hero
      }""",
"""      const net = freeNet(), me = net ? window.__mp.me & 1 : 0;
      for (const [iw, ew] of freeGames(M)) {
      if (H[iw + 0x41B0] !== 1) continue;                            // gameplay only
      for (let p = 0; p < (net ? 2 : 1); p++) {                      // online: both heroes (both are people)
        const hero = dv.getUint32(iw + 0x3C00 + 0x1AC * p, true);
        if (hero < 0x02000000 || hero >= 0x02040000) continue;
        const at = ew + (hero - 0x02000000) + 0x14, cur = dv.getUint32(at, true);
        if (cur === FREE_GAME) dv.setUint32(at, FREE_HOOK, true);   // always on: it also turns Frodo's crossbows (16 facings)
      }
      if (!freeOn()) H[ew + FREE_MB + 4 * me] = 0;                   // joystick 8 ways: the hook leaves his walk alone
      if (!net || me === 0) H[ew + FREE_MB + 3] = enemyChase() ? 1 : 0;   // v177: chasing enemies (online: the host's setting)
      }""")
# HD Backpack: each player's own game
rep("""        if (!M || !M.HEAPU8 || !M._rotk_iwram || (M._rotk_link_iwram && (!M._rotk_link_on() || (window.__mp && window.__mp.online)))) return hide();   // v179: local P2 games too
        const iw = M._rotk_iwram(), ew = M._rotk_ewram();""",
"""        if (!M || !M.HEAPU8 || !M._rotk_iwram || (M._rotk_link_iwram && (!M._rotk_link_on() || %s))) return hide();   // v179: local P2 games too; v180: online too
        const onl = !!(window.__mp && window.__mp.online), me = onl ? window.__mp.me & 1 : 0;
        const iw = onl ? M._rotk_link_iwram(me) : M._rotk_iwram(), ew = onl ? M._rotk_link_ewram(me) : M._rotk_ewram();""" % ONL)
# HD Backpack taps online: the press waits 3 frames so the box choice (CURREQ, sent as a page write) gets there first
rep("""    const press = (id, ms = 90) => { gi(id, 1); setTimeout(() => gi(id, 0), ms); };
    let el = null, last = "", ctx = null;""",
"""    const press = (id, ms = 90) => {
      if (window.__mp && window.__mp.sync) { setTimeout(() => { gi(id, 1); setTimeout(() => gi(id, 0), ms); }, 50); return; }
      gi(id, 1); setTimeout(() => gi(id, 0), ms);
    };
    let el = null, last = "", ctx = null;""")
open(dst, "w").write(s)
print("online features patched", len(s))
