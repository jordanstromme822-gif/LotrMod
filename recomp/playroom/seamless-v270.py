"""Play Room v270: put the current recomp/playroom/seamless.js into the page's <script id="seamlessJs"> (covered doors
to and from a big region: darkness closing in at a cave mouth, the outside fading into a building, no black screen).

python3 recomp/playroom/seamless-v270.py IN.html OUT.html
"""
import os, sys
src, out = sys.argv[1:3]
html = open(src, encoding='utf-8').read()
a = html.index('<script id="seamlessJs">\n') + len('<script id="seamlessJs">\n'); b = html.index('</script>', a)
js = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seamless.js'), encoding='utf-8').read()
if not js.endswith('\n'): js += '\n'
html = html[:a] + js + html[b:]
open(out, 'w', encoding='utf-8').write(html); print('ok', len(html))
