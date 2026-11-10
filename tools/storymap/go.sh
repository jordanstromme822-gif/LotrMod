L=$1; d=/tmp/rc/sm/L$L; mkdir -p $d; rm -f $d/dump.bin; cp fight.state $d/
printf 'load fight\npoke 030041F8 %x\npoke 030041F4 5\npoke 030041F0 81\n600 -\ndump 03003248 4\ndump 03004174 4\ndump 02030000 10000\ndump 02000000 40000\ndump 03000000 8000\n' $L > $d/s.txt
timeout 200 /tmp/rc/fx/run2 /tmp/rc/oh/rotk.gba $d/s.txt $d > $d/out.txt 2>&1
