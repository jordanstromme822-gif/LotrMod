# run.sh speed copies
P="950:030041F8:2f;950:030041F4:5;950:030041F0:81;1500:0203FF08:18;1500:0203FF04:ff;1500:0203FF10:6600000;1500:0203FF00:$2"
cd /tmp/rc/tg; S=$(date +%s.%N)
env ROTK_GOD=1 GBARECOMP_CPU_SPEED=$1 GBARECOMP_INPUT_REPLAY=in1.input ROTK_POKES="$P" ROTK_REPORT=1499,1560,1860 timeout 300 /tmp/rc/tb/build/RotkRecomp --bios bios.bin --rom game.gba --frames 1861 --dump-png /tmp/rc/tg/s$1_$2.png game.toml 2>/dev/null | grep REPORT | python3 -c "
import sys,re
L=[dict(re.findall(r'(\w+)=(\d+)',l)) for l in sys.stdin]
a,b=L[1],L[2]
print('speed $1 copies $2: level',a['level'],'spawned',a['spawned'],'objects',b['objects'],'game fps %.1f'%((int(b['gameframes'])-int(a['gameframes']))*60/300))"
echo "  wall $(echo "$(date +%s.%N) - $S" | bc) s"
