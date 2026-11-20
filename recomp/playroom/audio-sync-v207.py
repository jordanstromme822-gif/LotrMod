#!/usr/bin/env python3
"""Play Room: sound stays in step with the game, no slow drift or loop-like stutter (2026-11-20).

  python3 audio-sync-v207.py in.html out.html

Jordan (iPhone): "The audio isn't matching up with the game especially at the forge it's almost like it has a loop".
Measured in headless Chromium (Forge in Moria, CPU slowed 3x like a phone):
- The game's own sound is clean at the Forge (no repeated blocks, same beat as in the level), so the problem was how the
  page plays it.
- With the HD Forge / Shrine / Backpack page open, the page still drew the full HD picture every frame under it, though
  nobody can see it. On a slow phone that took the time the game needed: the game made ~72% of real-time sound and the
  sound queue ran dry 36 times in 8 s (the fade out, 60 ms wait, fade in pattern that sounds like a loop).
  Now the picture is not drawn while an HD page covers it: 98% of real time, 5 gaps.
- After any hiccup the game catches up and the queue fills; the old catch-up played only 1% faster above 0.14 s, so up
  to 0.4 s of lag could stay for tens of seconds (sound behind the game), then got cut with a jump.
  Now the speed follows the queue both ways (-1% .. +3%, aiming at 70 ms), and more than 0.2 s queued skips to 80 ms
  with a short cross-fade.
Works the same in 1-player, P2 and online (one page host, GbrHost, plays every mode's sound).
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)

# 1. no hidden HD picture while the HD Forge / Shrine / Backpack page covers it
rep('''      if (this.holdT && performance.now() < this.holdT) { this.pumpAudio(); return; }   // picture held still (Undo's redraw flip)
''', '''      if (this.holdT && performance.now() < this.holdT) { this.pumpAudio(); return; }   // picture held still (Undo's redraw flip)
      // v207 (Jordan: sound "isn't matching up ... especially at the forge"): the HD Forge / Shrine / Backpack page covers
      // the whole picture, so don't spend the phone's time drawing it; the game keeps full speed and its sound with it.
      if (window.__hdShopOn || window.__hdBpOn) { this.pumpAudio(); return; }
''')

# 2. speed follows the queue both ways (was: 1% faster above 0.14 s only)
rep('''          const step = rate / ac.sampleRate * (this.sQ > ac.sampleRate * 0.14 ? 1.01 : 1);''',
    '''          const step = rate / ac.sampleRate * (1 + Math.max(-0.01, Math.min(0.03, (this.sQ / ac.sampleRate - 0.07) * 0.3)));   // v207: aim at 70 ms queued''')

# 3. too much queued: skip to 80 ms with a cross-fade (was: > 0.4 s cut to 0.15 s, no fade)
rep('''if (this.n > sampleRate * 0.4) { while (this.n > sampleRate * 0.15 && this.q.length > 1) { const b = this.q.shift(); this.n -= b.length - this.off; this.off = 0; } }''',
    '''if (this.n > sampleRate * 0.2) { while (this.n > sampleRate * 0.08 && this.q.length > 1) { const b = this.q.shift(); this.n -= b.length - this.off; this.off = 0; } this.fade = 0; this.skips = (this.skips || 0) + 1; }''')
rep('''this.port.postMessage({ q: this.n, gaps: this.gaps });''', '''this.port.postMessage({ q: this.n, gaps: this.gaps, skips: this.skips || 0 });''')
rep('''node.port.onmessage = (e) => { this.sQ = e.data.q; this.aGaps = e.data.gaps; };''',
    '''node.port.onmessage = (e) => { this.sQ = e.data.q; this.aGaps = e.data.gaps; this.aSkips = e.data.skips; };''')
rep('''", gaps " + (H.aGaps || 0) + (H.sNode ? " (stream)" : "")''', '''", gaps " + (H.aGaps || 0) + ", skips " + (H.aSkips || 0) + (H.sNode ? " (stream)" : "")''')
open(dst, "w", encoding="utf-8").write(s)
print("ok")
