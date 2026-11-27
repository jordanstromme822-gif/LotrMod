"""Play Room v274: campfire travel (plan Phase 2). Puts the current recomp/playroom/seamless.js into the page's
<script id="seamlessJs"> (its travel cover: the place's name over black while the level changes) and
recomp/playroom/campfire.js into <script id="campfireJs"> right after it (lit campfires per saved hero, the Travel
button by a lit campfire, the list of lit campfires).

python3 recomp/playroom/campfire-v274.py IN.html OUT.html
"""
import os, sys
src, out = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
html = open(src, encoding='utf-8').read()
def body(name):
    js = open(os.path.join(here, name), encoding='utf-8').read()
    return js if js.endswith('\n') else js + '\n'
a = html.index('<script id="seamlessJs">\n') + len('<script id="seamlessJs">\n'); b = html.index('</script>', a)
html = html[:a] + body('seamless.js') + html[b:]
tag = '<script id="campfireJs">\n'
if tag in html:
    a = html.index(tag) + len(tag); b = html.index('</script>', a); html = html[:a] + body('campfire.js') + html[b:]
else:
    a = html.index('<script id="seamlessJs">\n'); b = html.index('</script>', a) + len('</script>')
    html = html[:b] + '\n' + tag + body('campfire.js') + '</script>' + html[b:]
open(out, 'w', encoding='utf-8').write(html); print('ok', len(html))
