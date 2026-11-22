# Recolor tools (2026-11-22)

Lore colours for the purple lands and the 8-minute sky cycle (Play Room v246).

- `render.py`: renders every level to palette-index images (`idx/L.npy`, `meta.pkl`) from the ROM (needs `tools/siege/romlib.py` + unicorn).
- `lib.py`, `recolor.py`, `mats.py`: OKLab/OKLCH helpers, hue-window rules, material ramps (earth, turf, granite, soot, night-haze ...).
- `plans.py`: colour plans per area. `X_O` = round 2 "organic" plans that went live in v246.
- `compose.py`: `new_palette(pal, plan, palp)` -> 256 BGR555 colours; `render2` before/after pictures; `sky_bank(L)`.
- `sky.py`: morning/noon/dusk/night sky keyframes (FREE lands, SHADOW for Mordor/Isengard, MORGULSKY for Morgul).
- `gen.py`: writes the page data (`recomp/playroom/lore-colors-v246.json`): new palettes per ROM address and each outside level's sky bank keyframes.
- `resid.py`: leftover-purple check per level.

Palette groups (ROM address: levels): Dunharrow 0x88b9a9c (30-35), Morgul 0x89f1464 (74-80), Isengard 0x894722c (50,51,55)
0x89595a4 (52,54,56) 0x8963c10 (53,57), Gorgoroth 0x88f93b8 (40-43), Shelob 0x8ad006c (115-117), Ice 0x8923334 (48),
Paths of the Dead 0x8a26460 (85-89), Balcony 0x89cb27c (68), White Mountains 0x8afabac (122-129).

Sky layers use a bank of the level's own BG palette (level entry +0x44 map, bank in the top nibble). Levels whose ground
also uses that bank (16-18, 28, 56, 90, 91, 103, 105) keep a still sky.
