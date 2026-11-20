"""Play Room v209: Sell All in the HD Forge / Shrine (Jordan, 2026-11-20: "change the leave button in the forge menu to
sell all, have it sell all inventory at the same time, make sure it prompts you to ask if you are sure first when you
select it and show the amount you will receive").
Page-only: replaces the v203 HD shop (shop-v203.js) with recomp/playroom/shop-v209.js. The button under the backpack is
Sell All (B still leaves the shop): it asks the game what each item is worth, shows the list and the total, asks
"Are you sure?", and on Yes empties the 12 backpack boxes and adds the gems at once.
Usage: shop-v209.py live.html out.html"""
import re, sys, os
src, out = sys.argv[1:3]
t = open(src).read()
a = t.index('  // v203 HD Forge / Shrine')
b = t.index('\n  })();', t.index('    window.__hdShopDbg', a)) + len('\n  })();')   # just the hdShop block (v206 statRefund follows it)
old = t[a:b]
assert old.count('(function hdShop()') == 1
css = re.search(r"el\.innerHTML = '<style>' \+\n(.*?)'</style><div class=\"pg lp\"></div><div class=\"pg rp\"></div>';", t, re.S).group(1)
assert '#hdBp' in css
css = css.replace('#hdBp', '#hdSh')
js = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shop-v209.js')).read()
assert js.count('/*CSS*/\n') == 1
js = js.replace('/*CSS*/\n', css)
t = t[:a] + js.rstrip('\n') + t[b:]
assert t.count('(function hdShop()') == 1
open(out, 'w').write(t)
print('ok', len(old), '->', len(js))
