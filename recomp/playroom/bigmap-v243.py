"""Play Room v243: engine that can keep a big map in ROM (tools/bigmap). Every existing level loads as before.

python3 recomp/playroom/bigmap-v243.py IN.html OUT.html
"""
import os, subprocess, sys
src, dst = sys.argv[1:3]
html = open(src, encoding='utf-8').read()
js = subprocess.check_output([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../tools/bigmap/bigmap.py'), '--js']).decode().rstrip('\n')


def once(old, new):
    global html
    assert html.count(old) == 1, (html.count(old), old[:80])
    html = html.replace(old, new)


once("      // All four Bonus Maps paths open (tools/unlockpaths.py).\n", js + "\n      // All four Bonus Maps paths open (tools/unlockpaths.py).\n")
once('const V = isLink ? "?v=236" : "?v=hd2";   // v236: faster engine build + rotk_smooth',
     'const V = isLink ? "?v=243" : "?v=hd2";   // v243: big-map stubs compiled in (tools/bigmap)   // v236: faster engine build + rotk_smooth')
open(dst, 'w', encoding='utf-8').write(html)
print('ok', len(html))
