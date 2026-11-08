#!/usr/bin/env python3
"""Phone version of the Play Room (docs/phone, served by GitHub Pages) and its private game pack.

usage: make-phone.py page <playroom index.html> <docs/phone dir>
       make-phone.py pack <solo wide dir> <link wide dir> <emu dir> <romdocs.json> <save.json> <out.bin> <version>

The page is the Play Room with phone.js in front (saves and the game file on the phone, no Claude account) and
Home Screen tags. The pack holds everything that comes from the game (engine builds, the player's game file and
saves) and is never put on the public site: the player picks it once and it is kept in the phone's cache.
"""
import json, os, struct, sys

HEAD = ('<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="RotK">'
        '<link rel="manifest" href="manifest.json"><link rel="apple-touch-icon" href="icon.png"><script src="phone.js"></script>')

def page(src, out):
    s = open(src, encoding="utf-8").read()
    assert s.count("</head>") >= 1
    s = s.replace("</head>", HEAD + "</head>", 1)
    s = s.replace("<title>Return of the King Play Room</title>", "<title>Return of the King</title>", 1)
    s = s.replace('<meta charset=utf8>', '<meta charset=utf8><script>if(!navigator.serviceWorker||!navigator.serviceWorker.controller||!localStorage.getItem("rotk-phone-pack"))location.replace("index.html")</script>', 1)
    open(os.path.join(out, "play.html"), "w", encoding="utf-8").write(s)

def pack(solo, link, emu, romdocs, save, out, version):
    files = []
    for n in ["bios.txt", "game.txt", "game-link.txt", "rotk.js", "rotk-0.wasm", "rotk-1.wasm"]:
        files.append(("wide/" + n, os.path.join(solo, n)))
    for n in ["rotk-link.js", "rotk-link-0.wasm", "rotk-link-1.wasm"]:
        files.append(("wide/" + n, os.path.join(link, n)))
    for root, _, names in os.walk(emu):
        for n in sorted(names):
            p = os.path.join(root, n)
            files.append(("emu/" + os.path.relpath(p, emu).replace(os.sep, "/"), p))
    docs = json.load(open(romdocs))
    docs["save-rotk-modded"] = json.load(open(save))
    blobs = [(p, open(f, "rb").read()) for p, f in files] + [("docs.json", json.dumps(docs, separators=(",", ":")).encode())]
    head = json.dumps({"version": version, "files": [{"p": p, "n": len(b)} for p, b in blobs]}).encode()
    with open(out, "wb") as o:
        o.write(b"RKPK1\n" + struct.pack("<I", len(head)) + head)
        for _, b in blobs: o.write(b)

if __name__ == "__main__":
    {"page": page, "pack": pack}[sys.argv[1]](*sys.argv[2:])
