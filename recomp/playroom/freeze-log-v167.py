# Play Room v167 (2026-11-11): when the 2-player game stops, the play log gets the engine's last lines, the last page error
# and an engine abort message (Jordan: 2-player froze in Helm's Deep on iPhone; not reproduced headless). Apply after frodo-traps-v166.py.
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:80]!r}")
    s = s.replace(old, new)
rep('''      window.__slog = slog;''', '''      window.__slog = slog;
      // Freeze clues (v167, Jordan 2026-11-11: the 2-player game stopped in Helm's Deep): the last page error is kept and
      // goes into the play log with "engine stopped".
      window.addEventListener("error", (e) => { try { window.__lastErr = String(e.message || e.error || "error").slice(0, 200); } catch (x) {} });
      window.addEventListener("unhandledrejection", (e) => { try { window.__lastErr = "promise: " + String(e.reason && (e.reason.message || e.reason)).slice(0, 200); } catch (x) {} });''')
rep('''      if (!wdSaid && now - wdT > 6000) { wdSaid = true; slog("engine stopped at frame " + f); say("The 2-player game stopped. Tap P2 to go back to 1 player."); }''',
'''      if (!wdSaid && now - wdT > 6000) {
        wdSaid = true;
        let extra = "";
        try { extra += " | engine says: " + (window.__wideLog || []).slice(-4).join(" / ").slice(0, 400); } catch (e) {}
        try { if (window.__lastErr) extra += " | page error: " + window.__lastErr; } catch (e) {}
        try { if (performance.memory) extra += " | js heap " + Math.round(performance.memory.usedJSHeapSize / 1e6) + " MB"; } catch (e) {}
        slog("engine stopped at frame " + f + extra); say("The 2-player game stopped. Tap P2 to go back to 1 player.");
      }''')
rep('''      const m = await e.create({ wasmBinary: e.wasm, noInitialRun: true, ''', '''      const m = await e.create({ wasmBinary: e.wasm, noInitialRun: true, onAbort: (w) => { try { window.__lastErr = "engine abort: " + String(w).slice(0, 200); log.push(window.__lastErr); } catch (x) {} }, ''')
open(dst, "w", encoding="utf-8").write(s); print("ok")
