"""Swap new Siege map data into a Play Room page that already has the Siege map (v197+).

python3 recomp/playroom/siege-swap.py LIVE.html NEW_BUILD.html OUT.html

NEW_BUILD.html is any page made by siege-v197.py with the new SIEGE_DIR. Only the three Siege lines
(map data, level entry, object entry) are taken from it; everything else comes from LIVE.html, so other
threads' changes on the live page are kept.
"""
import sys

live_p, new_p, out_p = sys.argv[1:4]
live = open(live_p, encoding='utf-8').read().split('\n')
new = open(new_p, encoding='utf-8').read().split('\n')


def find(lines, key):
    hits = [i for i, l in enumerate(lines) if key in l]
    assert len(hits) == 1, (key, len(hits))
    return hits[0]


for key in ('const SIEGE = ', '0x6A7B4);', '0x6C30C);'):
    live[find(live, key)] = new[find(new, key)]
open(out_p, 'w', encoding='utf-8').write('\n'.join(live))
print('ok')
