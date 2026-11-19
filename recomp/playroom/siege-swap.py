"""Swap new Siege map data into a Play Room page that already has the Siege map (v197+).

python3 recomp/playroom/siege-swap.py LIVE.html NEW OUT.html [--name "Levels list name"]

NEW is either the output folder of tools/siege/build.py (siege.bin, tables.bin) or any page made by
siege-v197.py. Only the three Siege lines (map data, level entry, object entry) are replaced, plus the
map's name in the Levels list with --name; everything else comes from LIVE.html, so other threads'
changes on the live page are kept.
"""
import base64, os, struct, sys

args = sys.argv[1:]
name = None
if '--name' in args:
    i = args.index('--name'); name = args[i + 1]; del args[i:i + 2]
live_p, new_p, out_p = args[:3]
live = open(live_p, encoding='utf-8').read().split('\n')


def find(lines, key):
    hits = [i for i, l in enumerate(lines) if key in l]
    assert len(hits) == 1, (key, len(hits))
    return hits[0]


if os.path.isdir(new_p):
    data = open(os.path.join(new_p, 'siege.bin'), 'rb').read()
    t = open(os.path.join(new_p, 'tables.bin'), 'rb').read()
    lv_at = struct.unpack('<I', t[:4])[0]; ob_at = struct.unpack('<I', t[0x50:0x54])[0]
    assert (lv_at, ob_at) == (0x6A7B4, 0x6C30C)
    new = {'const SIEGE = ': '        const SIEGE = Uint8Array.from(atob("' + base64.b64encode(data).decode() + '"), (c) => c.charCodeAt(0));',
           '0x6A7B4);': '        g.set(hexBytes("' + t[4:4 + 0x4C].hex() + '"), 0x6A7B4);',
           '0x6C30C);': '        g.set(hexBytes("' + t[0x54:0x60].hex() + '"), 0x6C30C);'}
else:
    lines = open(new_p, encoding='utf-8').read().split('\n')
    new = {k: lines[find(lines, k)] for k in ('const SIEGE = ', '0x6A7B4);', '0x6C30C);')}
for key, line in new.items():
    live[find(live, key)] = line
if name:
    i = find(live, '["Siege", [[45, "')
    live[i] = '    ["Siege", [[45, "' + name.replace('"', '\\"') + '"]]],'
open(out_p, 'w', encoding='utf-8').write('\n'.join(live))
print('ok')
