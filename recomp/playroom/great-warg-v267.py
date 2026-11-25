"""Play Room v267: the great warg is hoary silver instead of purple (2026-11-25).

python3 recomp/playroom/great-warg-v267.py IN.html OUT.html

The great warg (enemy kind 49, Isengard's warg pack leaders) has its own OBJ palette, palette id 28 (kind -> palette
table 0x0806D27C, palettes 0x082830B0 -> 0x082DD164), used by no other kind. Its pale lavender ramp shows as plain
purple on the HD picture. The page now writes a silver-grey ramp of the same brightness (warm in the shadows, like the
plain warg's fur; eyes and teeth, entries 13-15, kept) over it when it loads the game. The palette is ROM data that the
recompiled engine reads from the loaded game, so 1-player, P2 and online all get it.
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding='utf-8').read()
MARK = '      // v267: the great warg (kind 49) silver-grey, not purple (recomp/playroom/great-warg-v267.py).\n'
NEW = '1f7cdf7b9d6f3a63f85a954e5346f039ad314b25630c2a21081d5c434d46ff03'
OLD = '1f7cff7b9d7b3a77d872756e136ab069'   # the game's own first 8 entries, so a changed game is left alone
line = MARK + '      if (Array.from(game.subarray(0x2DD164, 0x2DD174), (b) => b.toString(16).padStart(2, "0")).join("") === "%s") game.set(hexBytes("%s"), 0x2DD164);\n' % (OLD, NEW)
if MARK in s:
    print('already there'); open(dst, 'w', encoding='utf-8').write(s); sys.exit()
anchor = '      // All four Bonus Maps paths open (tools/unlockpaths.py).\n'
assert s.count(anchor) == 1, 'anchor'
s = s.replace(anchor, line + anchor)
open(dst, 'w', encoding='utf-8').write(s); print('ok')
