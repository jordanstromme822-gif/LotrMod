# Bigger crossbow trap (v202)

Jordan, 2026-11-20: "Make trap image a little larger. Give the bolt a glowing whiteish blue tip and the string a blue
ish slight glow."

- `xbbig.py` makes `xbbig.bin` (16 facings, 24x24 pictures in 32x32 sprites, 512 bytes each, ROM 0x95000 in the
  freed Spanish text bank) from `tools/turn16/xb16.bin` (Scale3x, every second pixel), and `xbbig.json` (bolt tip =
  palette colour 10, bow = colour 12, per frame) for the page's glow.
- Page patch: `recomp/playroom/bolt-trap-v202.py`. It points crossbow.c's `xb_anim` (0x080852D0) and turn16's
  `xb16_anim` at the new pictures and the 16-frame records (data only; no engine rebuild).
- Found on the way: the Orc Head code was rebuilt after v171, so `xb_update` / `xb_anim` moved (0x08083105 /
  0x080852D0) and turn16's compiled check (0x08082231 / 0x08084408) stopped matching. Crossbows have been 8-way
  since then and the v171 warm ground glow was off. v202 brings the glow back; 16-facing turning needs turn16 rebuilt
  with the new addresses and the engine regenerated.
