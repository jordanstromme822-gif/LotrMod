"""Play Room v278: save on exit (plan Phase 2). Puts tools/autosave/autosave.bin into the page's Modded game (free
German text bank, 0x93000) with the state table pointing the gameplay (state 1) and Backpack (0x0A) updates
at it, right after the Orc Head block's own state table entries, and recomp/playroom/autosave.js into
<script id="autosaveJs"> after <script id="saveBackupJs">.

python3 recomp/playroom/autosave-v278.py IN.html OUT.html
"""
import os, struct, sys
src, out = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
tools = os.path.join(here, '..', '..', 'tools', 'autosave')
html = open(src, encoding='utf-8').read()
code = open(os.path.join(tools, 'autosave.bin'), 'rb').read()
sym = dict(l.split() for l in open(os.path.join(tools, 'autosave.sym')))
le = lambda a: struct.pack('<I', a).hex()
AT = 0x93000
assert len(code) < 0x400
anchor = 'game.set(hexBytes("75080808"), 0x6C8EC); // state table -> pause_upd\n'
assert html.count(anchor) == 1, html.count(anchor)
i = html.index(anchor); ind = html[html.rfind('\n', 0, i) + 1:i]
mark = '// v278 save on exit'
if mark in html:
    a = html.index(ind + mark); b = html.index(ind + '// v278 end\n', a) + len(ind + '// v278 end\n'); html = html[:a] + html[b:]
    i = html.index(anchor)
block = (f'{ind}{mark} (tools/autosave): the code, then the gameplay and Backpack updates go through it\n'
         f'{ind}game.set(hexBytes("{code.hex()}"), 0x{AT:X});\n'
         f'{ind}game.set(hexBytes("{le(int(sym["as_play"], 16) | 1)}"), 0x6C838); // state table -> as_play\n'
         f'{ind}game.set(hexBytes("{le(int(sym["as_bag"], 16) | 1)}"), 0x6C8A4); // state table -> as_bag (Backpack)\n'
         f'{ind}// v278 end\n')
j = i + len(anchor); html = html[:j] + block + html[j:]
js = open(os.path.join(here, 'autosave.js'), encoding='utf-8').read()
tag = '<script id="autosaveJs">\n'
if tag in html:
    a = html.index(tag) + len(tag); b = html.index('</script>', a); html = html[:a] + js + html[b:]
else:
    a = html.index('<script id="saveBackupJs">\n'); b = html.index('</script>', a) + len('</script>')
    html = html[:b] + '\n' + tag + js + '</script>' + html[b:]
open(out, 'w', encoding='utf-8').write(html); print('ok', len(html))
