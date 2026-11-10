const { chromium } = require('playwright'); const fs=require('fs');
const LV=+(process.argv[2]||46), OUT='/tmp/rc/cap/L'+LV; fs.mkdirSync(OUT,{recursive:true});
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:640,height:480}});
p.on('pageerror',x=>console.log('err',x.message));
await p.goto('http://localhost:8765/h.html?e=skin');
await p.waitForFunction(()=>window.ready||window.__err,null,{timeout:120000});
const press=async(k,ms=150)=>{await p.evaluate(k=>WideHost.keys=1023&~k,k);await p.waitForTimeout(ms);await p.evaluate(()=>WideHost.keys=1023);await p.waitForTimeout(300);};
await p.waitForTimeout(8000);
for(let i=0;i<14;i++){await press(8);await p.waitForTimeout(1200);}
for(let i=0;i<8;i++){await press(1);await p.waitForTimeout(1200);}
await p.evaluate((lv)=>{const iw=new Uint8Array(M.HEAPU8.buffer,M._rotk_iwram(),0x8000);iw[0x41F8]=lv;iw[0x41F4]=5;iw[0x41F0]=0x81;M._rotk_skin(1);},LV);
await p.waitForTimeout(9000);
for(let i=0;i<4;i++){await press(1);await p.waitForTimeout(800);}
const grab=async(n)=>{const r=await p.evaluate(()=>{const H=WideHost,d=H.d,u8=M.HEAPU8;const fr=H.front;const base=H.ptr+d.video+fr*d.videoStride;const u=new Uint32Array(u8.buffer);
 const w=u[base>>2],h=u[(base>>2)+1];const px=u8.slice(base+d.pixels,base+d.pixels+w*h*3);const tp=M._rotk_skin_slot(fr);const tags=new Uint8Array(u8.buffer,tp,w*h*4).slice();
 const vram=u8.slice(M._rotk_vram(),M._rotk_vram()+0x18000),pal=u8.slice(M._rotk_pal(),M._rotk_pal()+0x400);const iw=new Uint8Array(M.HEAPU8.buffer,M._rotk_iwram(),0x8000);
 const enc=a=>{let s='';for(let i=0;i<a.length;i+=8192)s+=String.fromCharCode.apply(null,a.subarray(i,i+8192));return btoa(s);};
 return {w,h,st:iw[0x41B0],lv:iw[0x41F8],px:enc(px),tags:enc(tags),vram:enc(vram),pal:enc(pal)};});
 for(const k of ['px','tags','vram','pal'])fs.writeFileSync(`${OUT}/${n}.${k}`,Buffer.from(r[k],'base64'));
 fs.writeFileSync(`${OUT}/${n}.json`,JSON.stringify({w:r.w,h:r.h,st:r.st,lv:r.lv}));return r;};
// pause engine while grabbing so all buffers match
const dirs=[16,32,64,128]; // right left up down
let n=0;
const path=[[16,1500],[128,1500],[32,1500],[64,1500],[16,3000],[128,3000],[32,3000],[64,3000],[16,5000],[64,2000],[32,5000],[128,5000]];
for(const [k,ms] of path){ for(let t=0;t<ms;t+=700){await p.evaluate(k=>WideHost.keys=1023&~k,k);await p.waitForTimeout(700);
  await p.evaluate(()=>{WideHost.keys=1023;M._rotk_pause(1)});await p.waitForTimeout(100);const r=await grab(n++);await p.evaluate(()=>M._rotk_pause(0));
  if(n%5==0)console.log(n,r.st,r.lv);} }
await p.screenshot({path:OUT+'/last.png'});
await b.close();})();
