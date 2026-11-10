set -e
cd /tmp/rc
node /mnt/project-files/engine-build/arrows-sized/buildrom.js "/mnt/project-files/Lord of the Rings, The_ The Return of the King/Lord of the Rings, The - The Return of the King (USA, Europe) (En,Fr,De,Es,It).gba" modded4.gba > build4.log 2>&1
sha1sum modded4.gba
bash solo4.sh > solo4.log 2>&1; echo solo exit $?
bash link4.sh > link4.log 2>&1; echo link exit $?
