// Free-angle joystick + 16 facings (test, Jordan 2026-11-11: "re draw the gaps in between the animation frames to make
// 360 degree motion look smooth", tried on Frodo). 1-player Wide only. The stick's exact screen angle goes to EWRAM
// 0x0203FFC0 (+0 bit 0 on, bit 1 held; +1 angle 0-255, 0 = up, clockwise) and the hero's update (object + 0x14) is
// pointed at the ROM hook 0x0809F001 (tools/turn16/turn16.c), which turns his walk to that angle after the game's own
// 8-way step and shows Frodo's in-between pictures (tools/turn16/gen16.py, ROM 0x0808A000). The d-pad still gets the
// nearest of the game's 8 directions, so everything else (walk state, attacks) works as before. Off: rotk-free = "0".
const FREE_HOOK = 0x0809F001, FREE_GAME = 0x080236B9, FREE_MB = 0x3FFC0;
const freeOn = () => { try { return localStorage.getItem("rotk-free") !== "0"; } catch (e) { return true; } };
const freeLabel = () => { const b = document.getElementById("freeSetup"); if (b) b.textContent = "Joystick: " + (freeOn() ? "Free 360°" : "8 ways"); };
window.__toggleFree = () => { try { localStorage.setItem("rotk-free", freeOn() ? "0" : "1"); } catch (e) {} freeLabel(); };
window.addEventListener("DOMContentLoaded", freeLabel);
setTimeout(freeLabel, 0);
// The solo Wide engine only (it has _rotk_ewram and no link), with the hook in its ROM.
const freeM = () => { const M = window.__wideM; return M && window.__turn16 && typeof M._rotk_ewram === "function" && !M._rotk_link_on ? M : null; };
window.__freeStick = (held, ang) => {
  const M = freeM(); if (!M) return;
  try { const e = M._rotk_ewram() + FREE_MB, H = M.HEAPU8; H[e] = freeOn() ? (held ? 3 : 1) : 0; if (held) H[e + 1] = ang & 255; } catch (e) {}
};
// Screen angle (0 = up, clockwise, 256 steps) -> the game's d-pad direction (0 = up, clockwise, 8 steps), through the
// same 16 facings the hook uses (the ground is squashed 2:1 on screen, so 'up-right' runs at 63 degrees).
window.__freeDir8 = (ang) => {
  const t = ang * Math.PI / 128, phi = ((Math.atan2(Math.sin(t), 2 * Math.cos(t)) * 180 / Math.PI) + 360) % 360;
  const f = Math.round(phi / 22.5) % 16;
  return !(f & 1) ? f >> 1 : f < 8 ? (f - 1) >> 1 : ((f + 1) >> 1) & 7;
};
window.__freeActive = () => !!(freeOn() && freeM());
setInterval(() => {
  const M = freeM(); if (!M) return;
  try {
    const H = M.HEAPU8, iw = M._rotk_iwram(), ew = M._rotk_ewram(), dv = new DataView(H.buffer);
    if (H[iw + 0x41B0] !== 1) return;                              // gameplay only
    const hero = dv.getUint32(iw + 0x3C00, true);
    if (hero < 0x02000000 || hero >= 0x02040000) return;
    const at = ew + (hero - 0x02000000) + 0x14, cur = dv.getUint32(at, true);
    if (freeOn() && cur === FREE_GAME) dv.setUint32(at, FREE_HOOK, true);
    else if (!freeOn() && cur === FREE_HOOK) { dv.setUint32(at, FREE_GAME, true); H[ew + FREE_MB] = 0; }
  } catch (e) {}
}, 8);
