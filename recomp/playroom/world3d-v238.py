# Play Room v238: the 3D World shows the hand-built Morgul mine area (picture 12) on the Crossroads screen (L76).
# The game's own maps/L76.webp stays as it is (the in-game seamless doors use it); the 3D World alone loads
# maps/x/L76.webp and maps/x/t/L76.webp. Usage: python3 world3d-v238.py index.html
import sys
p = sys.argv[1]; s = open(p).read()
old_t = 'loader.load("maps/t/L" + l + ".webp",'
old_f = 'loader.load("maps/L" + l + ".webp",'
assert s.count(old_t) == 1 and s.count(old_f) == 1
s = s.replace(old_t, 'loader.load((W3X[l] ? "maps/x/t/L" : "maps/t/L") + l + ".webp",')
s = s.replace(old_f, 'loader.load((W3X[l] ? "maps/x/L" : "maps/L") + l + ".webp",')
anchor = '    const loader = new THREE.TextureLoader();'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '\n    const W3X = { 76: 1 };   // v238: hand-built screens (game art re-laid), 3D World only')
open(p, 'w').write(s)
print("v238 applied")
