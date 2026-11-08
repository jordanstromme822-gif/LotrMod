#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
static struct mCore* c; static color_t* buf; static unsigned W,H;
static void nolog(struct mLogger* l,int a,enum mLogLevel lv,const char* f,va_list v){}
static struct mLogger L={.log=nolog};
int init(const char* rom,int save){mLogSetDefaultLogger(&L);c=mCoreFind(rom);if(!c)return -1;c->init(c);mCoreInitConfig(c,NULL);
 c->desiredVideoDimensions(c,&W,&H);buf=malloc(W*H*sizeof(color_t));c->setVideoBuffer(c,buf,W);
 if(!mCoreLoadFile(c,rom))return -2; if(save)mCoreAutoloadSave(c); c->reset(c);return 0;}
void step(int keys,int n){for(int i=0;i<n;i++){c->setKeys(c,keys);c->runFrame(c);}}
unsigned r8(unsigned a){return c->busRead8(c,a);} unsigned r16(unsigned a){return c->busRead16(c,a);} unsigned r32(unsigned a){return c->busRead32(c,a);}
void w8(unsigned a,unsigned v){c->busWrite8(c,a,v);} void w16(unsigned a,unsigned v){c->busWrite16(c,a,v);} void w32(unsigned a,unsigned v){c->busWrite32(c,a,v);}
void readblk(unsigned a,unsigned n,unsigned char* o){for(unsigned i=0;i<n;i++)o[i]=c->busRead8(c,a+i);}
void shot(const char* p){FILE*f=fopen(p,"wb");fprintf(f,"P6 %u %u 255\n",W,H);for(unsigned i=0;i<W*H;i++){uint32_t v=buf[i];unsigned char px[3]={v&0xff,(v>>8)&0xff,(v>>16)&0xff};fwrite(px,1,3,f);}fclose(f);}
int savest(const char* p){size_t n=c->stateSize(c);void*s=malloc(n);c->saveState(c,s);FILE*f=fopen(p,"wb");fwrite(s,1,n,f);fclose(f);free(s);return n;}
int loadst(const char* p){size_t n=c->stateSize(c);void*s=malloc(n);FILE*f=fopen(p,"rb");if(!f)return -1;fread(s,1,n,f);fclose(f);c->loadState(c,s);free(s);return 0;}
