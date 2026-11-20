"""Play Room v203: HD Forge / Shrine fixes (Jordan, 2026-11-20, phone video of a Forge: "There are no items for sale, you
could randomly generate items there" / "the leave button serves no purpose and isn't accessible" / "notice how I can't
access certain things at the forge").
Page-only: replaces the v181 HD shop (recomp/playroom/item-menu-v181.py) with recomp/playroom/shop-v203.js:
- the page's own cursor over every box (goods, gear for sale, 12 backpack boxes, Leave), moved by the joystick / d-pad /
  arrow keys; the game's cursor follows it (closed loop), so A buys / sells through the game as before;
- Forges sell 6 random pieces of gear rolled from the game's item tables for the hero shopping (up to their level),
  priced 5x the game's sell price; bought gear goes into the first free backpack box;
- Leave can be reached and pressed.
Usage: shop-v203.py live.html out.html"""
import re, sys, os
src, out = sys.argv[1:3]
t = open(src).read()
a = t.index('  // v181 HD Forge / Shrine')
b = t.index('\n  (function itemPanel() {')
old = t[a:b]
# the HD Backpack's look (its style sheet, with #hdBp -> #hdSh), as v181 did
css = re.search(r"el\.innerHTML = '<style>' \+\n(.*?)'</style><div class=\"pg lp\"></div><div class=\"pg rp\"></div>';", t, re.S).group(1)
assert '#hdBp' in css
css = css.replace('#hdBp', '#hdSh')
js = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shop-v203.js')).read()
assert js.count('/*CSS*/\n') == 1
js = js.replace('/*CSS*/\n', css)
t = t[:a] + js.rstrip('\n') + '\n' + t[b:]
assert t.count('(function hdShop()') == 1
open(out, 'w').write(t)
print('ok', len(old), '->', len(js))
