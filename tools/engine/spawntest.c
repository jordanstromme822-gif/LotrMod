typedef unsigned int u32; typedef unsigned short u16; typedef unsigned char u8;
#define F(a,t) ((t)((a)|1))
typedef void (*v_fn)(void); typedef void (*g_fn)(u32);
/* 0x0203FF00: request count, +4 group (0xFF = all groups with type 29), +8 spread px, +0xC spawned total */
void hook(void){
  F(0x080391C4,v_fn)();
  volatile u32 *f=(u32*)0x0203FF00;
  if(!f[0]) return;
  u32 n=f[0]; f[0]=0;
  u8 *blob=*(u8**)0x03003234; u16 ng=*(u16*)blob;
  u8 *hero=*(u8**)0x03003C00;
  int hx=*(int*)(hero+0xAC), hy=*(int*)(hero+0xB0);
  int k=0;
  for(u32 rep=0;rep<n;rep++)
  for(u32 g=0;g<ng;g++){
    if(f[1]!=0xFF && f[1]!=g) continue;
    u8 *gb=blob+*(u16*)(blob+2+2*g); u32 m=gb[0]; int has=0;
    for(u32 i=0;i<m;i++){ u8*r=gb+*(u16*)(gb+2+2*i); if(((f[4]>>*(u16*)(r+8))&1)) has=1; }
    if(!has) continue;
    for(u32 i=0;i<m;i++){ u8*r=gb+*(u16*)(gb+2+2*i); if(((f[4]>>*(u16*)(r+8))&1)) *(u32*)r=0; }
    F(0x0800C0EC,g_fn)(g);
    for(u32 i=0;i<m;i++){ u8*r=gb+*(u16*)(gb+2+2*i); u8*o=*(u8**)r;
      if(!((f[4]>>*(u16*)(r+8))&1) || !o) continue;
      int dx=((k&7)-4)*(int)f[2], dy=(((k>>3)&7)-4)*(int)f[2]; k++;
      int x=hx+(dx<<16), y=hy+(dy<<16);
      *(int*)(o+0xA4)=x;*(int*)(o+0xAC)=x;*(int*)(o+0xCC)=x;
      *(int*)(o+0xA8)=y;*(int*)(o+0xB0)=y;*(int*)(o+0xD0)=y; }
  }
  f[3]+=k;
}
