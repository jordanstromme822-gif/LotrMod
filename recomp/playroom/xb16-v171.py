#!/usr/bin/env python3
"""Play Room v171 page patch (on live v170): Frodo's crossbow traps turn through 16 facings.
Replaces the free-angle hook's code at 0x9F000 with the new turn16.bin (it now turns crossbows too), adds the
crossbow's 16 pictures (xb16.bin, our own pixel art) at 0x94400, and keeps the hook on the hero in the solo Wide
engine whatever the joystick chip says (with 8 ways it only clears the stick mailbox, so his walk is the game's own).
Usage: xb16-v171.py in.html out.html turn16.bin xb16.bin"""
import re, sys
src, dst, t16, x16 = sys.argv[1:5]
s = open(src).read()
code, pics = open(t16, "rb").read(), open(x16, "rb").read()
assert len(code) <= 0x1000 and len(pics) == 2048
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x9F000\); // free-angle hook \(tools/turn16/turn16\.c\)',
               lambda m: 'game.set(hexBytes("%s"), 0x9F000); // free-angle hook (tools/turn16/turn16.c)\n'
                         '      game.set(hexBytes("%s"), 0x94400); // crossbow trap, 16 facings (tools/turn16/xb16.py)' % (code.hex(), pics.hex()), s)
assert k == 1, k
s, k = re.subn(r"( *)if \(freeOn\(\) && cur === FREE_GAME\) dv\.setUint32\(at, FREE_HOOK, true\);\n *else if \(!freeOn\(\) && cur === FREE_HOOK\) \{ dv\.setUint32\(at, FREE_GAME, true\); H\[ew \+ FREE_MB\] = 0; \}",
               lambda m: m.group(1) + "if (cur === FREE_GAME) dv.setUint32(at, FREE_HOOK, true);   // always on: it also turns Frodo's crossbows (16 facings)\n"
                         + m.group(1) + "if (!freeOn()) H[ew + FREE_MB] = 0;                          // joystick 8 ways: the hook leaves his walk alone", s)
assert k == 1, k
open(dst, "w").write(s)
print("crossbow 16 facings patched")
