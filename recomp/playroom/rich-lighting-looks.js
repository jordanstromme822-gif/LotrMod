  // Looks for Rich lighting: one per group of levels (the same groups as the Siege picker). L = look values.
  const LIGHT_LOOKS = (() => {
    const base = { ShadowTint: [0.0, 0.0, 0.02], HiTint: [0.03, 0.02, 0.0], GlowTint: [1.0, 0.85, 0.65], FogCol: [0.1, 0.1, 0.12], Gain: [1.04, 1.03, 1.0],
      Sat: 1.15, GlowK: 1.0, Clarity: 0.7, Relief: 0.9, Vig: 0.22, Fog: 0.0, Lift: 0.0, Amount: 1.0, Sun: 0.10, Thr: 0.55, Water: 1.0, WaterCol: [0.16, 0.42, 0.62] };
    const L = (o) => Object.assign({}, base, o);
    const looks = {
      menu: L({ Water: 0.0, Relief: 0.0, Clarity: 0.25, Vig: 0.0, Sun: 0.0, GlowK: 0.5, Sat: 1.06, Amount: 0.8 }),
      Woods: L({ ShadowTint: [-0.01, 0.02, 0.035], HiTint: [0.03, 0.035, 0.0], Gain: [1.03, 1.06, 0.98], Sat: 1.18, Sun: 0.16, Vig: 0.26 }),
      Plains: L({ ShadowTint: [0.0, 0.0, 0.03], HiTint: [0.06, 0.04, 0.0], Gain: [1.06, 1.04, 0.97], Sat: 1.14, Sun: 0.18 }),
      "River & water": L({ WaterCol: [0.12, 0.45, 0.55], ShadowTint: [-0.02, 0.015, 0.05], HiTint: [0.03, 0.03, 0.02], Gain: [1.0, 1.04, 1.06], Sat: 1.16, GlowTint: [0.8, 0.95, 1.0] }),
      "Ships & docks": L({ WaterCol: [0.12, 0.38, 0.55], ShadowTint: [-0.01, 0.01, 0.05], HiTint: [0.05, 0.03, 0.0], Gain: [1.02, 1.02, 1.03], Sat: 1.1, Fog: 0.05, FogCol: [0.35, 0.42, 0.5] }),
      "Camps & houses": L({ ShadowTint: [0.0, 0.0, 0.03], HiTint: [0.07, 0.04, 0.0], Gain: [1.07, 1.03, 0.95], GlowK: 1.2, Thr: 0.5 }),
      "Snow & ice": L({ ShadowTint: [-0.02, 0.01, 0.07], HiTint: [0.02, 0.03, 0.05], Gain: [1.02, 1.05, 1.09], Sat: 1.0, GlowK: 0.7, GlowTint: [0.8, 0.9, 1.0], Thr: 0.62, Fog: 0.06, FogCol: [0.7, 0.78, 0.9] }),
      Lava: L({ ShadowTint: [0.05, -0.005, -0.02], HiTint: [0.03, 0.0, -0.01], Gain: [1.03, 0.97, 0.92], Sat: 1.15, GlowK: 1.15, GlowTint: [1.0, 0.5, 0.2], Thr: 0.6, Vig: 0.34, Fog: 0.05, FogCol: [0.3, 0.06, 0.02] }),
      Wasteland: L({ ShadowTint: [0.03, 0.0, 0.0], HiTint: [0.06, 0.03, -0.01], Gain: [1.05, 1.0, 0.94], Sat: 1.0, GlowK: 1.2, GlowTint: [1.0, 0.6, 0.35], Vig: 0.32, Fog: 0.06, FogCol: [0.25, 0.14, 0.1] }),
      Mountains: L({ WaterCol: [0.12, 0.36, 0.6], ShadowTint: [-0.01, 0.0, 0.04], HiTint: [0.04, 0.03, 0.01], Gain: [1.03, 1.03, 1.03], Clarity: 0.7, Fog: 0.04, FogCol: [0.55, 0.6, 0.7] }),
      "Red rock": L({ ShadowTint: [0.03, 0.0, 0.01], HiTint: [0.06, 0.03, 0.0], Gain: [1.06, 1.0, 0.95], Sat: 1.12, Clarity: 0.65, Vig: 0.28 }),
      Fortress: L({ ShadowTint: [-0.005, 0.0, 0.035], HiTint: [0.05, 0.035, 0.01], Gain: [1.05, 1.03, 0.99], Clarity: 0.7, GlowK: 1.1, Sun: 0.14, Vig: 0.26 }),
      City: L({ ShadowTint: [-0.005, 0.005, 0.04], HiTint: [0.05, 0.04, 0.02], Gain: [1.05, 1.04, 1.02], Clarity: 0.65, Sun: 0.16 }),
      "Dwarf halls": L({ ShadowTint: [0.0, 0.0, 0.04], HiTint: [0.07, 0.04, 0.0], Gain: [1.06, 1.02, 0.94], GlowK: 1.5, GlowTint: [1.0, 0.7, 0.4], Thr: 0.45, Vig: 0.42, Sun: 0.0, Fog: 0.05, FogCol: [0.03, 0.03, 0.06] }),
      Caves: L({ ShadowTint: [-0.01, 0.0, 0.05], HiTint: [0.06, 0.04, 0.0], Gain: [1.04, 1.02, 0.98], GlowK: 1.4, GlowTint: [1.0, 0.75, 0.45], Thr: 0.45, Vig: 0.45, Sun: 0.0, Fog: 0.06, FogCol: [0.02, 0.03, 0.06] }),
      Ruins: L({ ShadowTint: [0.0, 0.01, 0.04], HiTint: [0.04, 0.03, 0.0], Sat: 1.05, Clarity: 0.65, Vig: 0.3, Fog: 0.05, FogCol: [0.4, 0.42, 0.45] }),
      level: base,
    };
    const GROUPS = [["Woods", [19, 20, 21, 22, 23, 36, 37, 38, 59, 60]], ["Plains", [92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 109, 110, 112, 114]], ["River & water", [0, 2, 3, 39]], ["Ships & docks", [14, 15, 24, 25]], ["Camps & houses", [1, 61, 108, 111, 113]], ["Snow & ice", [48, 122, 123, 124, 125, 126, 127, 128, 129]], ["Lava", [16, 17, 18, 28, 29, 42]], ["Wasteland", [26, 27, 40, 41, 43, 50, 51]], ["Mountains", [6, 7, 8, 10, 12, 13, 74, 75, 76, 77, 78, 79, 80]], ["Red rock", [30, 31, 32, 34]], ["Fortress", [4, 5, 9, 46, 47, 53, 55, 56, 57, 58]], ["City", [63, 67, 68, 69, 71, 72, 73, 90, 91]], ["Dwarf halls", [49, 81, 82, 83, 84]], ["Caves", [52, 54, 85, 86, 87, 88, 89, 115, 116, 117]], ["Ruins", [121]]];
    const byLevel = {}; for (const [g, ls] of GROUPS) for (const n of ls) byLevel[n] = g;
    return { looks, forLevel: (n) => looks[byLevel[n]] || looks.level, names: byLevel };
  })();
  // Which look to use: the level's group while playing (state 1) and in its pause menu (16), the soft menu look elsewhere.
  setInterval(() => {
    try {
      const M = window.__wideM; if (!M || !M._rotk_iwram) return;
      const b = M._rotk_iwram(), st = M.HEAPU8[b + 0x41B0], lv = M.HEAPU8[b + 0x41F8];
      if (st === 1) window.__rotkLook = LIGHT_LOOKS.forLevel(lv);
      else if (st !== 16) window.__rotkLook = LIGHT_LOOKS.looks.menu;
    } catch (e) {}
  }, 400);
  // Rich lighting on/off: setup screen button, or G on a keyboard while playing.
  const lightOn = () => { try { return localStorage.getItem("rotk-light") !== "0"; } catch (e) { return true; } };
  const lightSet = (on) => { try { localStorage.setItem("rotk-light", on ? "1" : "0"); } catch (e) {} const b = document.getElementById("lightSetup"); if (b) b.textContent = "Rich lighting: " + (on ? "On" : "Off"); };
  window.addEventListener("DOMContentLoaded", () => lightSet(lightOn()));
  setTimeout(() => lightSet(lightOn()), 0);
  window.__toggleLight = () => lightSet(!lightOn());
  window.addEventListener("keydown", (e) => { if ((e.key === "g" || e.key === "G") && document.body.classList.contains("playing") && !e.repeat) window.__toggleLight(); });
