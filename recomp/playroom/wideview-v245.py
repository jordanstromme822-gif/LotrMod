"""Play Room v245: engine relinked so the wide view also reads level maps kept in ROM (big joined maps, v243/v244).

python3 recomp/playroom/wideview-v245.py IN.html OUT.html

Only bumps the engine cache key (?v=243 -> ?v=245) so phones fetch the new rotk-link files. The engine change is in
recomp/link/link_main.cpp (rotk_view::level_mem, H from 0x03005864); relink with relink.sh (no regen needed).
"""
import sys
src, dst = sys.argv[1:3]
html = open(src, encoding='utf-8').read()
assert html.count('"?v=243"') == 1
open(dst, 'w', encoding='utf-8').write(html.replace('"?v=243"', '"?v=245"'))
print('ok')
