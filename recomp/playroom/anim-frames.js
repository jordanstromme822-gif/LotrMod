// Extra animation frames (Graphics phase 4). Off unless localStorage rotk-anim === "1".
// While the game holds a frame, object +0x20 counts down and +0x22 is the frame on screen
// (the anim stepper 0x080022E4). The second half of that count shows the smear cell from
// skin/anim.json; the first half keeps the cell the tile key already selected.
let ANIM = null, animHalf = 0, animHalfAt = 0, animPeriod = 1, animFrame = -1;
function animOn(){ try { return localStorage.getItem("rotk-anim") === "1"; } catch (e) { return false; } }
function animLabel(){ const b = document.getElementById("animSetup"); if (b) b.textContent = "Extra frames: " + (animOn() ? "On" : "Off"); }
function animSet(on){ try { localStorage.setItem("rotk-anim", on ? "1" : "0"); } catch (e) {} if (on) animLoad(); animLabel(); }
window.__toggleAnim = () => animSet(!animOn());
window.addEventListener("keydown", (e) => {
  const t = e.target;
  if ((e.key === "j" || e.key === "J") && !e.repeat && document.body.classList.contains("playing")
      && !(t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"))) window.__toggleAnim();
});
window.addEventListener("DOMContentLoaded", animLabel);
animLabel();
function animLoad(){
  if (ANIM) return;
  fetch("skin/anim.json").then((r) => r.ok ? r.json() : 0).then((j) => { ANIM = j || 0; }).catch(() => { ANIM = 0; });
}
function animHero(){
  try {
    const M = window.__wideM; if (!M || !M._rotk_iwram) return null;
    const H8 = M.HEAPU8, ib = M._rotk_iwram(), dv = new DataView(H8.buffer);
    if (H8[ib + 0x41B0] !== 1) return null;
    const ptr = dv.getUint32(ib + 0x3C00, true);
    const o = ptr >= 0x2000000 && ptr < 0x2040000 ? M._rotk_ewram() + (ptr - 0x2000000) : ptr >= 0x3000000 && ptr < 0x3008000 ? ib + (ptr - 0x3000000) : 0;
    if (!o) return null;
    return { shown: H8[o + 0x22], timer: H8[o + 0x20] };
  } catch (e) { return null; }
}
function animSample(){
  const now = performance.now();
  if (now - animHalfAt < 12) return animHalf;
  animHalfAt = now;
  const h = animHero();
  if (!h) { animHalf = 0; return 0; }
  if (h.shown !== animFrame) { animFrame = h.shown; animPeriod = Math.max(1, h.timer || 1); }
  else if (h.timer > animPeriod) animPeriod = h.timer;
  const along = 1 - Math.min(1, h.timer / animPeriod);
  animHalf = along >= 0.5 ? 1 : 0;
  return animHalf;
}
window.__rotkAnimCell = (key, cell) => {
  if (!animOn() || !ANIM || !ANIM.byKey) return cell;
  const pair = ANIM.byKey[key];
  if (!pair) return cell;
  const alt = pair[animSample()];
  const c = (typeof CRISP !== "undefined" && CRISP.map) ? CRISP.map.get(alt) : 0;
  return c || cell;
};
if (animOn()) animLoad();
