# usage: regen.sh <page rom> <tag>   -> /tmp/rc/b2/gen<tag>, /tmp/rc/b2/one<tag>, copies to site6
set -e
ROM=$1; T=$2; cd /tmp/rc/b2
head -c 16777216 $ROM > link$T.gba
S=$(sha1sum link$T.gba | cut -c1-40)
python3 - "$S" "$T" <<'P'
import sys, re
sha, T = sys.argv[1], sys.argv[2]
t = open('/home/user/lotrmod/recomp/link/game-link.toml').read()
t = t.replace('dd6d504c587ce487c983968f4f01748457b30ed8', sha).replace('path = "bios.bin"', 'path = "/tmp/rc/b2/bios.bin"').replace('path = "game.gba"', 'path = "/tmp/rc/b2/link%s.gba"' % T)
open('/tmp/rc/b2/game-link%s.toml' % T, 'w').write(t)
P
python3 /home/user/lotrmod/recomp/orcslots/linkfuncs.py /home/user/lotrmod/tools/orcslots/orcslots.sym game-link$T.toml
python3 /home/user/lotrmod/recomp/link/turn16funcs.py /home/user/lotrmod/tools/turn16/turn16.sym game-link$T.toml
python3 /home/user/lotrmod/recomp/link/feelfuncs.py game-link$T.toml
python3 /home/user/lotrmod/tools/bigmap/bigmapfuncs.py game-link$T.toml
rm -rf gen$T && gbarecomp/build/gba_recompile --rom link$T.gba --config game-link$T.toml --codegen-shards 8 --out gen$T > gen$T.log 2>&1
python3 /home/user/lotrmod/recomp/orcslots/genpatch.py gen$T /home/user/lotrmod/tools/orcslots/orcslots.sym | tail -1
rm -rf one$T && mkdir one$T
GEN=/tmp/rc/b2/gen$T O=/tmp/rc/b2/one$T bash /tmp/rc/b2/build-shards.sh
O=/tmp/rc/b2/one$T bash /tmp/rc/b2/relink.sh
# published toml (generic paths, placeholder sha, 320 view)
sed -e "s/$S/dd6d504c587ce487c983968f4f01748457b30ed8/g" -e 's#path = "/tmp/rc/b2/bios.bin"#path = "bios.bin"#' -e "s#path = \"/tmp/rc/b2/link$T.gba\"#path = \"game.gba\"#" -e 's/^view_width = .*/view_width = 320/' game-link$T.toml > one$T/game-link.txt
cp one$T/game-link.txt /tmp/rc/site6/wide/game-link.txt
echo REGEN $T DONE
