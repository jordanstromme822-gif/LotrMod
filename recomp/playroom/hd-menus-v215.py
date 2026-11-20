#!/usr/bin/env python3
"""Play Room v215 (Jordan, 2026-11-20: "Modernize and update all menus"): HD title and pause menus drawn by the page.

  hd-menus-v215.py in.html out.html

Adds hd-menus.js as its own <script> at the end of the page (replaced whole if it is there already).
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()
js = open(os.path.join(HERE, "hd-menus.js"), encoding="utf-8").read().rstrip("\n")
block = '<script id="hdMenusJs">\n' + js + "\n</script>\n"
if 'id="hdMenusJs"' in s:
    s = re.sub(r'<script id="hdMenusJs">.*?</script>\n', lambda m: block, s, count=1, flags=re.S)
else:
    assert s.count("</body>") == 1
    s = s.replace("</body>", block + "</body>")
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
