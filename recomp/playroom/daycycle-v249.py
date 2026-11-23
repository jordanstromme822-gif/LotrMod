"""v249 page step: day and night like Valheim (Jordan 2026-11-23: "Could we do valhiems?").

python3 daycycle-v249.py IN.html OUT.html

A 30-minute cycle of play time instead of 8: morning 5 min, noon 13, dusk 5, night 7, each change fading over 2
minutes. The clock still runs on saved play time (rotk-playT), so it carries over between sessions; levels with no
clock (caves, Moria, Mordor, windowless rooms) are unchanged. window.__dayT / __sunT still pin the clock for tests.
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding='utf-8').read()

old_dayT = 'const dayT = () => { const t = typeof window.__dayT === "number" ? window.__dayT : playT; return ((t % 480) + 480) % 480; };'
new_dayT = ('const CYC = 1800, PH = [300, 780, 300, 420], FADE = 120;   // v249: morning 5, noon 13, dusk 5, night 7 min (Valheim-like)\n'
            '    const dayT = () => { const t = typeof window.__dayT === "number" ? window.__dayT : playT; return ((t % CYC) + CYC) % CYC; };')
assert s.count(old_dayT) == 1, 'dayT'
s = s.replace(old_dayT, new_dayT)

old_w = '''      const p = dayT() / 120, w = [0, 0, 0, 0];
      for (let i = 0; i < 4; i++) { let d = Math.abs(p - (i + 0.5)); d = Math.min(d, 4 - d); const x = Math.min(1, Math.max(0, (0.75 - d) / 0.5)); w[i] = x * x * (3 - 2 * x); }
      return w;'''
new_w = '''      // v249: each phase holds its full weight, crossing over FADE seconds centred on every change
      const t = dayT(), w = [0, 0, 0, 0];
      let b = 0;
      for (let i = 0; i < 4; i++) {
        const s0 = b, e0 = b + PH[i]; b = e0;
        let d = Math.min(t - s0, e0 - t);                       // inside the phase: distance to its nearer edge
        if (t < s0 || t >= e0) d = -Math.min(Math.abs(t - s0), Math.abs(t - e0), Math.abs(t + CYC - e0), Math.abs(s0 + CYC - t));
        const x = Math.min(1, Math.max(0, (d + FADE / 2) / FADE)); w[i] = x * x * (3 - 2 * x);
      }
      const sum = w[0] + w[1] + w[2] + w[3] || 1;
      return w.map((v) => v / sum);'''
assert s.count(old_w) == 1, 'phaseW'
s = s.replace(old_w, new_w)

old_sun = 'const t = typeof window.__sunT === "number" ? ((window.__sunT % 480) + 480) % 480 : dayT(), day = t < 360, u = day ? t / 360 : (t - 360) / 120;   // v247: sun over morning-dusk, moon at night'
new_sun = ('const DAY = PH[0] + PH[1] + PH[2];   // v249: the sun crosses morning to dusk, the moon the night\n'
           '      const t = typeof window.__sunT === "number" ? ((window.__sunT % CYC) + CYC) % CYC : dayT(), day = t < DAY, u = day ? t / DAY : (t - DAY) / (CYC - DAY);')
assert s.count(old_sun) == 1, 'sunNow'
s = s.replace(old_sun, new_sun)
s = s.replace('// v247: morning, noon, dusk and night, 2 minutes each of play, fading over a minute into the next',
              '// v247: morning, noon, dusk and night (v249: 5, 13, 5 and 7 minutes of play, fading over 2 minutes)')
open(dst, 'w', encoding='utf-8').write(s)
print('day cycle v249 ok')
