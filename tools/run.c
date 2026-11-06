// Headless mGBA runner: ./run rom script outdir
// script lines: "<frames> <keys>" hold keys for that many frames; keys joined with +:
//   A B SEL START, U D LT RT (d-pad up/down/left/right), L R (shoulders), - for none
// "shot <name>" writes outdir/name.ppm ; "ram <name>" dumps EWRAM+IWRAM
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/interface.h>
#include <mgba/core/log.h>
#include <stdarg.h>
#include <stdio.h>
#include <mgba/debugger/debugger.h>
#include <mgba/internal/arm/arm.h>
static struct mCore* gcore; static struct mDebugger* dbg; static int hits;
static void entered(struct mDebugger* d, enum mDebuggerEntryReason r, struct mDebuggerEntryInfo* info){struct ARMCore* cpu=gcore->cpu; if(hits<4000) printf("WATCH addr=%08x pc=%08x lr=%08x new=%x r0=%08x r1=%08x r2=%08x r3=%08x r4=%08x r5=%08x r6=%08x r7=%08x\n",info?info->address:0,cpu->gprs[15],cpu->gprs[14],info?info->type.wp.newValue:0,cpu->gprs[0],cpu->gprs[1],cpu->gprs[2],cpu->gprs[3],cpu->gprs[4],cpu->gprs[5],cpu->gprs[6],cpu->gprs[7]); if(r==DEBUGGER_ENTER_BREAKPOINT && hits<4000){uint32_t sp=cpu->gprs[13]; printf("  STK"); int n=0; for(uint32_t ad=sp;ad<0x03007F00&&n<12;ad+=4){uint32_t v=gcore->busRead32(gcore,ad); if(v>=0x08000000&&v<0x0a000000&&(v&1)){printf(" %08x",v);n++;}} printf("\n");} hits++; d->state=DEBUGGER_RUNNING;}
static void nolog(struct mLogger* l,int c,enum mLogLevel lv,const char* f,va_list a){(void)l;(void)c;(void)lv;(void)f;(void)a;}
static struct mLogger L={.log=nolog};
#include <stdlib.h>
#include <string.h>
static int keymask(const char* s){int m=0;
 char buf[128]; strncpy(buf,s,127); buf[127]=0;
 for(char* t=strtok(buf,"+");t;t=strtok(NULL,"+")){
  if(!strcmp(t,"A"))m|=1;else if(!strcmp(t,"B"))m|=2;else if(!strcmp(t,"SEL"))m|=4;else if(!strcmp(t,"START"))m|=8;
  else if(!strcmp(t,"RT"))m|=16;else if(!strcmp(t,"LT"))m|=32;else if(!strcmp(t,"U"))m|=64;else if(!strcmp(t,"D"))m|=128;
  else if(!strcmp(t,"R"))m|=512;else if(!strcmp(t,"L"))m|=256;} // libmgba core: bit 8 = L, bit 9 = R
 return m;}
int main(int argc,char**argv){
 if(!getenv("MLOG")) mLogSetDefaultLogger(&L);
 struct mCore* core=mCoreFind(argv[1]); gcore=core; if(!core){puts("no core");return 1;}
 core->init(core); mCoreInitConfig(core,NULL);
 unsigned w,h; core->desiredVideoDimensions(core,&w,&h);
 color_t* buf=malloc(w*h*sizeof(color_t)); core->setVideoBuffer(core,buf,w);
 if(!mCoreLoadFile(core,argv[1])){puts("load fail");return 1;}
 core->reset(core);
 FILE* sc=fopen(argv[2],"r"); char line[256]; long frame=0;
 while(fgets(line,sizeof line,sc)){
  char a[64],b[128]; b[0]=0; if(sscanf(line,"%63s %127s",a,b)<1) continue;
  if(!strcmp(a,"shot")){char p[512];snprintf(p,512,"%s/%s.ppm",argv[3],b);FILE*f=fopen(p,"wb");fprintf(f,"P6 %u %u 255\n",w,h);
   for(unsigned i=0;i<w*h;i++){uint32_t c=buf[i];unsigned char px[3]={c&0xff,(c>>8)&0xff,(c>>16)&0xff};fwrite(px,1,3,f);}fclose(f);continue;}
  if(!strcmp(a,"watch")){ if(!dbg){dbg=calloc(1,sizeof(struct mDebugger)); dbg->type=DEBUGGER_CUSTOM; dbg->entered=entered; mDebuggerAttach(dbg,core); dbg->state=DEBUGGER_RUNNING;} char c[64]; int span=1; sscanf(line,"%*s %*s %d",&span); if(span<1)span=1; uint32_t ad=strtoul(b,0,16); for(int k=0;k<span;k++){struct mWatchpoint wp={0}; wp.address=ad+k; wp.segment=-1; wp.type=WATCHPOINT_WRITE; dbg->platform->setWatchpoint(dbg->platform,&wp);} (void)c; continue;}
  if(!strcmp(a,"break")){ if(!dbg){dbg=calloc(1,sizeof(struct mDebugger)); dbg->type=DEBUGGER_CUSTOM; dbg->entered=entered; mDebuggerAttach(dbg,core); dbg->state=DEBUGGER_RUNNING;} struct mBreakpoint bp={0}; bp.address=strtoul(b,0,16); bp.segment=-1; bp.type=BREAKPOINT_HARDWARE; dbg->platform->setBreakpoint(dbg->platform,&bp); continue;}
  if(!strcmp(a,"stack")){struct ARMCore* cpu=core->cpu; uint32_t sp=cpu->gprs[13]; printf("STACK %s pc=%08x lr=%08x sp=%08x:",b,cpu->gprs[15],cpu->gprs[14],sp); for(uint32_t ad=sp;ad<0x03007F00;ad+=4){uint32_t v=core->busRead32(core,ad); if(v>=0x08000000&&v<0x08400000&&(v&1)) printf(" %08x",v);} printf("\n"); continue;}
  if(!strcmp(a,"peek")){uint32_t ad=strtoul(b,0,16); printf("PEEK %08x:",ad); for(int k=0;k<16;k++) printf(" %04x",core->busRead16(core,ad+2*k)); printf("\n"); continue;}
  if(!strcmp(a,"dump")){uint32_t ad,n; sscanf(line,"%*s %x %x",&ad,&n); char p[512];snprintf(p,512,"%s/%s.bin",argv[3],"dump");FILE*f=fopen(p,"ab"); for(uint32_t k=0;k<n;k++){unsigned char v=core->busRead8(core,ad+k);fwrite(&v,1,1,f);} fclose(f); continue;}
  if(!strcmp(a,"save")){size_t n=core->stateSize(core);void*st=malloc(n);core->saveState(core,st);char p[512];snprintf(p,512,"%s/%s.state",argv[3],b);FILE*f=fopen(p,"wb");fwrite(st,1,n,f);fclose(f);free(st);continue;}
  if(!strcmp(a,"load")){size_t n=core->stateSize(core);void*st=malloc(n);char p[512];snprintf(p,512,"%s/%s.state",argv[3],b);FILE*f=fopen(p,"rb");if(!f){printf("no state %s\n",p);return 1;}fread(st,1,n,f);fclose(f);core->loadState(core,st);free(st);continue;}
  if(!strcmp(a,"ram")){char p[512];snprintf(p,512,"%s/%s.ram",argv[3],b);FILE*f=fopen(p,"wb");
   for(uint32_t ad=0x02000000;ad<0x02040000;ad++){unsigned char v=core->busRead8(core,ad);fwrite(&v,1,1,f);}
   for(uint32_t ad=0x03000000;ad<0x03008000;ad++){unsigned char v=core->busRead8(core,ad);fwrite(&v,1,1,f);}
   fclose(f);continue;}
  int n=atoi(a); int k=(b[0]&&strcmp(b,"-"))?keymask(b):0;
  for(int i=0;i<n;i++){core->setKeys(core,k); if(dbg) mDebuggerRunFrame(dbg); else core->runFrame(core);frame++;}
 }
 printf("ran %ld frames\n",frame); core->deinit(core); return 0;}
