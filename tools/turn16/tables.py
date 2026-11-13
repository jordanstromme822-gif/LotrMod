"""Write tables.h: SIN (Q14, 256 steps, 0 = up, clockwise on screen) and F16 (screen angle -> facing 0-15).
The game's 8 facings are 45 degrees apart in the ground plane, which the screen shows squashed 2:1
(the 'up-right' walk goes 63.4 degrees on screen), so facing = round(atan2(sx, 2 * cy) / 22.5)."""
import math, os
D = os.path.dirname(os.path.abspath(__file__))
sin = [round(16384 * math.sin(2 * math.pi * a / 256)) for a in range(256)]
f16 = []
for a in range(256):
    t = 2 * math.pi * a / 256
    phi = math.degrees(math.atan2(math.sin(t), 2 * math.cos(t))) % 360
    f16.append(int(round(phi / 22.5)) % 16)
with open(os.path.join(D, 'tables.h'), 'w') as f:
    f.write('/* made by tables.py */\n')
    f.write('static const short SIN[256] = {%s};\n' % ','.join(map(str, sin)))
    f.write('static const unsigned char F16[256] = {%s};\n' % ','.join(map(str, f16)))
print(f16)
