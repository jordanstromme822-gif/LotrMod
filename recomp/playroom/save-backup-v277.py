"""Play Room v277: save backups on the account (plan Phase 2, before save on exit). Puts
recomp/playroom/save-backup.js into <script id="saveBackupJs"> after <script id="campfireJs">.

python3 recomp/playroom/save-backup-v277.py IN.html OUT.html
"""
import os, sys
src, out = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
html = open(src, encoding='utf-8').read()
js = open(os.path.join(here, 'save-backup.js'), encoding='utf-8').read()
tag = '<script id="saveBackupJs">\n'
if tag in html:
    a = html.index(tag) + len(tag); b = html.index('</script>', a); html = html[:a] + js + html[b:]
else:
    a = html.index('<script id="campfireJs">\n'); b = html.index('</script>', a) + len('</script>')
    html = html[:b] + '\n' + tag + js + '</script>' + html[b:]
open(out, 'w', encoding='utf-8').write(html); print('ok', len(html))
