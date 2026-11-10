# OAM sprite reader for mGBA dumps (VRAM 0x18000 + palette 0x400 + OAM 0x400)

SIZES = {0: [(8,8),(16,16),(32,32),(64,64)], 1: [(16,8),(32,8),(32,16),(64,32)], 2: [(8,16),(8,32),(16,32),(32,64)]}
def sprites(D):
  vram=D[:0x18000]; oam=D[0x18400:0x18800]
  for i in range(128):
    a0,a1,a2=[int.from_bytes(oam[i*8+k:i*8+k+2],'little') for k in (0,2,4)]
    if a0&0x200 and not a0&0x100: continue
    sh,sz=a0>>14,a1>>14
    if sh==3: continue
    w,h=SIZES[sh][sz]; y=a0&255; x=a1&511; t=a2&0x3ff; bank=a2>>12; c256=(a0>>13)&1; hf=(a1>>12)&1; vf=(a1>>13)&1
    if y>=160: y-=256
    if x>=256: x-=512
    img=np.zeros((h,w),int)
    for ty in range(h//8):
      for tx in range(w//8):
        tt=t+(ty*(w//8)+tx)*(2 if c256 else 1); off=0x10000+tt*32
        a=np.frombuffer(vram[off:off+(64 if c256 else 32)],np.uint8)
        idx=a.reshape(8,8) if c256 else np.stack([a&15,a>>4],1).reshape(8,8)
        img[ty*8:ty*8+8,tx*8:tx*8+8]=idx
    if hf: img=img[:,::-1]
    if vf: img=img[::-1]
    yield dict(i=i,x=x,y=y,w=w,h=h,t=t,bank=bank,c256=c256,img=img,prio=(a2>>10)&3)
