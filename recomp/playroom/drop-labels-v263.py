#!/usr/bin/env python3
"""Play Room v263 (part 1): item names on the ground, Diablo 2 style (drop-labels.js, its own <script id="dropLabelsJs">,
replaced whole if it is there already). See the comment at the top of drop-labels.js.

  drop-labels-v263.py in.html out.html
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()
js = open(os.path.join(HERE, "drop-labels.js"), encoding="utf-8").read()
tag = '<script id="dropLabelsJs">\n' + js + '</script>\n'
if '<script id="dropLabelsJs">' in s:
    s = re.sub(r'<script id="dropLabelsJs">.*?</script>\n', lambda m: tag, s, count=1, flags=re.S)
else:
    assert s.count("</body></html>") == 1
    s = s.replace("</body></html>", tag + "</body></html>")
open(dst, "w", encoding="utf-8").write(s)
print("ok v263 drop labels")
