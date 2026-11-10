# Return of the King: GBARecomp experiment

A trial run of [GBARecomp](https://github.com/mstan/gbarecomp) on the original
US/Europe ROM (BLRE, SHA-1 `ec3d126d37ea6e2ad7030d8a99cf87c6e46c03fd`), done
2026-11-07 on Linux. This turns the GBA code into native C++ instead of
emulating it. **No ROM or BIOS is included here.**

## Result

- The recompiler found 11,344 game functions. The generated code compiles.
- With the open-source [Cult-of-GBA BIOS](https://github.com/Cult-of-GBA/BIOS)
  and the runtime's BIOS HLE, the native build boots to the language screen,
  runs the logos, title menu, hero select and story slides, and plays the
  first level (Aragorn walks, attacks, in-level dialogue shows). It ran headless
  at about 195 frames per second.
- The first build crashed entering the level: the game runs code it copies
  from ROM into IWRAM. The `[[code_copy]]` entries in `game.toml` (found by
  comparing live IWRAM with the ROM in mGBA) and the `[[extra_func]]` entries
  the runtime proposed fixed that.
- Not checked: sound, saving, later levels, 2-player, the Modded ROM patches.
  About 160 million instructions per 7,000 frames still go through the
  runtime's interpreter, so more `[[extra_func]]` work would make it fully native.

## Rebuild

1. Clone gbarecomp next to this folder as `gbarecomp/` (with submodules) and
   build its `gba_recompile` target.
2. `GBARECOMP_CORE=gbarecomp/build/gba_recompile python3 gbarecomp/tools/cli.py build --rom <your rom> --output port --config game.toml`
3. Copy `port/generated` here, then `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build`.
4. `GBARECOMP_INPUT_REPLAY=first-level.input ./build/RotkRecomp --bios <bios.bin> --rom <your rom> --frames 5300 --dump-png out.png game.toml`

`first-level.input` presses through the menus and story into the first level
(KEYINPUT values, active low, per frame).

## 60 fps smoothing (2026-11-07)

The game draws a new picture every other VBlank (30 fps). `gbarecomp-smooth60.patch`
adds `FrameSmoother` to the runtime: when a new picture arrives it first shows an
in-between picture (world layers scrolled halfway, world sprites shifted with the
camera, HUD left alone), then the real one, so the camera glides at 60 fps with one
VBlank of delay. The world layers here scroll coarsely (fine scroll 0..7, map redrawn
a tile over), so a halfway view outside 0..7 is drawn from the previous frame's map.
It only kicks in when re-rendering the new frame from the snapshot matches the real
picture. `GBARECOMP_SMOOTH=0` turns it off; `GBARECOMP_SMOOTH_TEST=dir,start,count`
dumps real (`r_`) and shown (`s_`, `m` = in-between) frames from headless runs.
Apply with `git apply` inside the gbarecomp clone (base 351572f).

## Zoomed-out view (2026-11-07)

`main-modded.cpp` widens levels to 320x160. The game keeps only a 31x21-tile window
of BG2 (foreground) and BG3 (ground) in VRAM, rebuilt from a block map (u16 block per
32x32 px; layer A map `*0x03005FB4` / set `*0x03005FBC`, layer B map `*0x0300586C` /
set `*0x03005FC0`, width u16 `0x03005878`, camera `0x03005880`). Each frame the VRAM
window is matched against the block map to anchor it; the PPU margin provider then
reads margin tiles from the level. BG1 (sky) wraps, BG0 (HUD) stays native, non-level
screens get black bars. Sprites: the game skips OAM pieces with x > 255; the PC ROM
patch at 0x08002F90 (`adds r0,r5,#0; adds r0,#0x40; lsrs r0,r0,#6; cmp r0,#6; bhi`)
allows up to x < 384, and raw 240..383 is decoded as the right margin. PC ROM sha1
88f9075bcba049d51c693f98173c677873d7e04f (regenerate with the same game.toml + new sha).
The smoothing patch now also covers the wide view (`g_ws_render_io`,
`g_ws_margin_scroll_override` in gba_ppu).

## 4:3 view (2026-11-07)

Levels now render 320x240 (`view_geometry` adds 40 px above and below). The HUD
(BG0 rows 120..159) is remapped to the bottom of the canvas, and the PC ROM also
patches 0x08002F88 (`movs r0,#0x84`) so sprite pieces reach y=200; raw y 160..200 is
the bottom margin. PC ROM sha1 dd6d504c587ce487c983968f4f01748457b30ed8.

## Phone Play Room: "Wide 4:3, 60 fps" (2026-11-07)

The same engine runs in the Play Room page on phones (no threads or SharedArrayBuffer needed).

- `gbarecomp-pc-and-web.patch` (replaces the smooth60 patch; includes it): single-threaded browser build.
  The run loop becomes an `emscripten_set_main_loop` frame callback (present-in-place off), no blocking sleeps,
  every 8th smoothing picture verified, wide frames shown at full size.
- `web/pc-web.toml`: game config with extra recompiled code. The game's sound mixer lives in IWRAM and patches its own
  `ldrb ..., asr #5` to `asr #4` at boot, so the generator is run on a copy of the PC ROM with those 8 bytes already
  patched (`modded-pc-gen.gba`, see the 0x08FFAB40.. bytes), and the mixer region is one `code_copy` 0x03000B38..0x0300115C.
  Without this the mixer ran in the interpreter every frame (2x slower).
- `main-modded.cpp`: tile provider now remembers the last tile per layer (big win in the wide renderer).
- `web/build.sh`, `web/link.sh`, `web/shim.cpp`: emscripten 3.1.6 build (needs `web/compat.h` for std::bit_cast).
- The page builds the PC ROM itself from the Play Room's Modded game (two cull patches at 0x2F88/0x2F90) and writes its
  SHA-1 into the config, so custom hero stats work. Save = the account copy (`save-rotk-modded`).
- Speed on the test machine (2.1 GHz Xeon VM, headless Chromium): ~55 fps in levels, 60 on menus.

### Wide view v70 (2026-11-07): sprite flicker fix and Sharp HD

- **Flicker fix** (`frame_smooth.h`, in the patch): the 60 fps in-between picture used to shift every
  sprite that changed by half the camera step. The hero follows the camera, so on frames where his
  animation changed he jumped back and forth by a few pixels (looked like flicker). Now every sprite of
  the new frame is matched to the nearest sprite of the previous frame with the same shape, size and
  palette; touching pieces with the same palette form one group that takes the most common step, and the
  group is drawn halfway between its old and new spot. Unmatched groups move with the halfway camera.
- **Sharp HD** (`web/sharphd.js`, pasted into the Play Room page): the Classic picture chain (scene
  pass `rotk-enhance`, then ScaleFX passes 0-4 at 3x) run with WebGL2. Shaders are the page's own
  `SCALEFX_PRESET` / `ROTK_ENHANCE_GLSL`, compiled as `#version 300 es` with VERTEX/FRAGMENT defines.
  PassPrev2 = output of pass 1, PassPrev5 = output of pass 0; passes 1-2 use RGBA16F when renderable.
  If WebGL2 or a shader fails, the page draws plain pixels with a 2D canvas. If the picture rate stays
  under 40/s for two 4-second windows, the page switches to plain pixels (still WebGL) for that session.

### Wide view v71 (2026-11-07): even frame timing

Jordan saw stutter and shaking on iPhone. The web tick counted game frames from the wall clock at each
display refresh, so timer jitter gave 2-0-2 patterns (two game frames on one refresh, none on the next),
and with 60 fps in-between pictures that shows as shaking. Now, when the display runs at about 60 Hz
(average refresh 15.6-17.8 ms), the tick runs exactly one game frame per refresh (2 only if more than 2.5
frames behind). Otherwise it rounds the clock count, at most 2. The game then runs 0.45% fast; the page
plays sound 1% faster while more than 0.14 s is queued. `rotk_tick_stats()` (shim) exposes counts of
ticks with 0/1/2 frames and resets; the page writes a "wide:" line to the private save-log doc every
30 s (pictures/s, screen Hz, 0/1/2 counts, picture mode), at most 12 per session.

### Wide view v82 (2026-11-08): even 60 fps steps

- Heroes walk about 3 pixels per game frame (shown as 2 screen refreshes). The in-between picture used whole
  pixels, so the steps came out 1 then 2. `frame_smooth.h` now draws the in-between picture twice (half step rounded
  down, then up) and averages them, so the steps are 1.5 and 1.5. Camera-locked sprites (the hero) are the same in
  both, so they stay sharp. `GBARECOMP_SMOOTH_BLEND=0` turns the averaging off.
- Backward jump fix: the world layers scroll by redrawing the map one tile over, so a 4-pixel move left and right
  looked the same from the fine scroll alone, and every few steps the in-between picture went the wrong way.
  `coarse_step()` now compares the old and new tile maps to see which way the map was redrawn.
- Checked natively with `GBARECOMP_INPUT_REPLAY` (walk script into Moria) and `GBARECOMP_SMOOTH_TEST`:
  left/down walking measures 1.5/1.5/2/2 per refresh (was 2/1 and, left, wrong-way jumps).

## v87 steady poses (2026-11-08)

Jordan saw the load-game heroes bob. When a character changes pose, its sprite pieces are re-laid,
so they "matched" the old pieces with a fake step and the in-between picture drew the new pose a few
pixels off. Now a step is trusted only when most pieces agree, and when the camera is still and a
piece's graphics changed (tile number or streamed tile data), the group is drawn where the new frame
has it. Patch: `smooth-v87-steady-poses.patch` (on top of the v82 smoothing).

## v92 smooth fades (2026-11-08)

Jordan asked for Smooth 60 everywhere. A native walk (walk2.input, `GBARECOMP_SMOOTH_WHY=1` prints why a
picture got no in-between frame) showed levels already smoothed; fades were the gap (80 skipped for
brightness/blend changes). The in-between picture now uses halfway BLDY/BLDALPHA, so fades step evenly
(80 -> 15 skipped). Patch file updated (same name, cumulative on top of v82).

### Options without Quick Skill Select (Play Room v110, 2026-11-08)

`tools/noquickskill.py` hides the Options row and makes the cursor step over it. The generated code of
both Wide engines (1 player `pcgame2/generated`, 2 player `mp/gen`) has the same three calls pointed at
the helpers, so no regeneration is needed: in `recompiled_007.cpp` `_blt_08036A2E = 0x0809ED00u`, in
`recompiled_003.cpp` `_blt_08036B38 = 0x0809ED0Au`, in `recompiled_002.cpp` `_blt_08036E84 = 0x0809ED12u`.
The helpers are not recompiled; they run in the interpreter (bridged) and call back into recompiled code.
Only those three shards were rebuilt; the page loads the engines with `?v=110` so a cached old `.js`
is never paired with the new `.wasm`.

### Simpler setup, online from Multiplayer, walk speed (Play Room v111, 2026-11-08)

The setup screen is only the game file, Download game (owner) and Play game: always the modded game, Wide,
Smooth 60. The hero/skill/mod editors are gone (saved stats and skills still apply). Host/Join moved into
the game's Multiplayer menu (`playroom/online-menu.js`); online games still run in the Classic picture.
Speed boosts now also speed up the walk cycle (`playroom/walk-speed.js`): measured walk speed is 3.0 px/tick,
+25 speed 3.75, +100 about 5.06 (cap), and with the page's extra steps px per walk step stays ~3.0.
Engines unchanged from v110.

### Grab button, B only hits, Auto/P2 in the pause menu (Play Room v112, 2026-11-08)

In play the Undo button is Grab (`playroom/grab-button.js`): it presses the game's R (pick up, open a chest or the
Shrine, talk) with L let go, and walks to items up to 22 px away first. It reads Open next to an unopened chest or
the Shrine, Full when the backpack is full, else Grab. B only hits; R in play only casts its skill (L held), and
flips tabs in menus. Auto and P2 press the game's R themselves, so they still pick up and open chests. Undo forgets
an item as soon as the screen changes (play, Skills, Attributes); its Backpack redraw flip (R then L) now runs
behind a held picture with the sound off (`window.__wideHold`), since writing the game's own redraw flags did not
redraw the items. Auto and P2 buttons show only in the game's pause menu (state 16). Engines unchanged.

### Online 2-player in Wide, walk steps of 5% (Play Room v113, 2026-11-08)

Online games now use the 2-player Wide engine (`playroom/online-wide.js`), with the same lockstep as the Classic
link: each page runs both games and only buttons travel through the room. `link/link_main.cpp` adds an online
mode: `ROTK_LINK_NET=1` runs a frame only when the page queues both players' buttons (`rotk_link_push`,
`rotk_link_queued`), `ROTK_LINK_SHOW` picks the game shown and heard (0 host, 1 guest), and both games mix
their sound in full so both pages hold the same memory (`rotk_link_hash`, compared every 120 frames).
Tested with two headless players at 40 ms latency: hashes matched for 1500+ frames, both in the same level.
Classic is the fallback if the engine can't load. The P2 helper still works with the new build (`?v=113`).
The walk speed-up now goes in steps of 5% speed, up to +75%.

### Shop Undo, P2 in the paused level, pause-menu buttons (Play Room v114, 2026-11-08)

Undo of a sale in the Shrine (state 20) put the item and gems back in memory, but the shop only draws them when
it opens, so the page now closes the shop (B) and opens it again (Grab) behind a held picture (`playroom/undo.js`).
Tested in Moria by moving the hero next to the Shrine (hero +0xAE/+0xB2 in both games). P2 now joins in the level
the game was paused in (the page remembers the level byte 0x030041F8 seen in play and the link engine swaps it in
at the path screen, `rotk_link_level`); tested level 76. After P2 joins, the sound stays off for 4 s and fades in.
Auto sits under P2 in the pause menu when the paused level is Moria (the level byte reads 0 for a frame as the
pause menu opens, so that no longer clears it). Upright A is a third smaller; sideways buttons are spread evenly.

### Grab / Full over herbs and food (Play Room v115, 2026-11-08)

Standing over an item (within 22 px), the Grab button reads Full only when it can't be taken: food (15, 16, 19)
at full health, herbs (17, 18, 20-24) when both herb pouches hold 10, gear (25+) with a full backpack
(`playroom/grab-label.js`). Tested by changing a dropped item's type byte (+0x60) in both games.
P2 sound check: recordings of the same level (76) solo and with P2 show one sound stream (about 60 buffers a
second, P1's game only) and the same spectrum; P2's game is drained and never played.

### P2 and online back to the full wide view, faster 2-player engine (Play Room v116, 2026-11-08)

Jordan: "P2 back to full wide screen smooth". The 2-player picture (P2 helper and online) uses the same view width
as solo Wide again (P2: chosen from the game area's shape, online: 320 on both pages so they stay identical) and
fills the game area; v103's 240-wide boxed picture is gone. Link engine `?v=116`.
Engine (`link/engine-speed-v116.patch`): the two games ran in tiny slices, about 13,000 handovers a frame, because
every instruction that the slice check didn't recognise ended a slice. Most were the game's sound mixer in IWRAM
(`ldrb rX, [r5, r7, asr #16]`: only LSL #0-4 register offsets were accepted) and DMA register writes for
graphics copies. Now every immediate shift is accepted, and DMA register reads and writes are inside a slice
(an immediate copy only when source and destination are plain memory and no IRQ is asked for). About 2,300
handovers a frame; headless top speed 68 -> about 100 frames a second. Online games still hash the same.
The frame smoother also handles a picture every 3rd VBlank (two in-between pictures at a third and two thirds);
measured while walking with P2 the game draws an even 30 pictures a second, so it rarely applies. The play log
shows in-between counts for the 2-player engine now too. `GBA_SESSION_PROFILE=1` prints why slices end.

### Phone version, full screen from the Home Screen (2026-11-08)

Jordan wanted to play sideways without the Claude app's bar. A page inside Claude can't hide it and iPhones don't
let a page go full screen, so `docs/phone/` (GitHub Pages: https://jordanstromme822-gif.github.io/LotrMod/phone/)
is the Play Room (`play.html`, made by `phone/make-phone.py page`) with `phone.js` standing in for the Claude
account: saves and the game file live in the phone's IndexedDB, with Back up / Restore saves buttons (a JSON file).
The public site holds no game: the engine builds, the game file and a copy of the saves come from a private game
pack (`make-phone.py pack`, project files `phone/rotk-phone-pack.bin`) that the player picks once; `sw.js` serves
`wide/` and `emu/` from the phone's cache. A newer pack never overwrites saves already on the phone. Online games
need the Claude Play Room (no room service here); P2 works.

### Orc Head slots (Play Room v117, 2026-11-08)

Jordan: "create 4 backpack slots underneath the inventory slots that can only hold 1 orc head item", with Orc
Heads giving their +1 Courage only from those slots. The ROM patch is `tools/orcslots.py` (code in
`tools/orcslots/`, see `docs/findings.md`). The Wide engines can't see ROM code changes, so
`orcslots/genpatch.py <generated dir> <orcslots.sym>` edits the generated C++ to call the hooks: six BL
second halves get a fixed target (AC24 re-apply, save unpack, title clear, two frame hooks, the A error sound)
and four sites become a call into a stub (keepsake check 0x0802DBE0, save pack 0x0803CC08, cursor move
0x0802CC60, A press 0x0802A854). Every hook returns to its call site, so the interpreter runs them and the
native code goes on as before. Applied to both the solo and the 2-player builds (shards 000, 001, 003, 004,
006, 007); engines `?v=117`. Tested in the Wide engine: two heads moved in (count 0 → 1 → 2, Courage 35 → 36 → 37),
picture and text as in mGBA, closing the backpack keeps both.

### Orc Head slots work like equipment slots (Play Room v119, 2026-11-08)

Jordan: "the orc head slots should work like equipment slots except only for orc heads". Equip in an Orc Head's
item menu puts it in the next free slot; A on a filled slot opens Unequip / Discard. Three more bl targets
(menu A 0x0802A9DA, description 0x0802AA06, discard 0x0802AA56) and two more call blocks (0x0802CCC4, 0x0802C5FC)
in `orcslots/genpatch.py`; shard 002 now changes too. The code grew, so every hook address moved: re-run genpatch
on the untouched generated shards, not on already patched ones (a patched call block is skipped, so it would keep
the old address). Engines `?v=119`.

### Orc Head tiers (Play Room v120, 2026-11-08)

Jordan: normal, magic and rare Orc Heads with rolled bonuses, new drop odds and caps (see `tools/orcslots.py`).
The code moved to the French text bank (0x7F000), so every hook address changed. `orcslots/genpatch.py` adds 16 bl
targets (item rolls, names, descriptions, EEPROM slot read/write, the gameplay frame) and 4 call blocks (drop routine
0x0803A6EC, treasure caps 0x0803A746 and 0x0802EF32, gem cap 0x0803AF54). Some of those sites are in functions the
generator didn't emit (the solo build lacks 0x08014B9A, 0x0802EF32/0x0802EF3E; neither has 0x0803CD14); those run
in the interpreter, which already sees the ROM patch. The link message cases are table data, so they need nothing.
All 8 shards change now (005 too); re-run genpatch on the untouched shards. Engines `?v=120`.

### Regenerating quivers (Play Room v121, 2026-11-08)

Jordan: "3% chance on drop to regenerate whatever amount of quiver they have at 1 per second". Same code as the
Orc Heads (`tools/orcslots/`). `orcslots/genpatch.py` adds 6 bl targets: the 4 shot calls of 0x0802C410 and the
2 arrow match checks 0x0802EB08 (the solo build lacks one of them; the interpreter runs it). Re-run genpatch on the
untouched shards. Engines `?v=121`.

### Frodo's crossbows (Play Room v125, 2026-11-09)

Jordan: Frodo's Snare places a small crossbow that shoots the nearest foe (10 bolts, 1-3 crossbows by skill
level), and Frodo gets 1 arrow slot whose arrows the bolts use (`tools/orcslots/crossbow.c`). It adds no call
sites: the skill table entry (0x6E974) points at the new handler, and the crossbow's update and the bolts' touch are
object function pointers, so the solo engine runs them in the interpreter and the 2-player engine compiles them
(`orcslots/linkfuncs.py`; its data list now names the crossbow's picture and tables). The hook code grew, so re-run
genpatch, linkfuncs and the 2-player regeneration. Engines `?v=125`.

### Frodo's skill rework (Play Room v126, 2026-11-09)

Jordan: Knife Toss stuns and bounces, Galadriel's Cloak becomes Quick Drop (sets down every crossbow, cooldown),
knives and bolts pass through foes under Ring's Persuasion, and Frodo's heavy armor goes back to normal (boots
stay). The new skill handlers (0x6E94C, 0x6E99C) need no call sites; Quick Drop's cooldown and Crossbow requirement
add 5 bl sites (the game's can-cast check at 0x08023898 / 0x080293F0 / 0x080431F8 / 0x080433E2 and the Skills page
buy at 0x08041FBC, genpatch BL list). Engines `?v=126`.

### Bolt Trap icons and item text (Play Room v127, 2026-11-09)

Snare is renamed Bolt Trap, and Frodo's Bolt Trap and Quick Drop icons are crossbows (`tools/orcslots/skillicons.py`; the
page's button icon sheet has the same pictures). On the Backpack, Legolas and Frodo read item text under their arrow
slots (3 lines, scrolling a line a second when longer). The hook code moved, so the engines are rebuilt: `?v=127`.

### Crossbow sounds (Play Room v128, 2026-11-09)

A crossbow now only plays the bow shot (sound 0x40) when it fires; its hit, break and set-down sounds are gone
(`tools/orcslots/crossbow.c`). The hook code changed size, so the engines are rebuilt: `?v=128`.

### Regenerating arrows refill to 99 (2026-11-10)

Jordan: a regenerating quiver stopped at the count it dropped with. Now it refills to 99 (QFULL in
`tools/orcslots/orcslots.c`; the pack form is 0x80 | 99). The hook code is 40 bytes shorter, so every hook after it
moved: re-run genpatch.py / linkfuncs.py and rebuild both engines. `tools/orcslots/pagejs.py <page.html>` rewrites the
page's Orc Head block (code hex, bl lines, link cases, state table entries) from orcslots.bin/.sym.

### Item menu in the item text panel (Play Room v158, 2026-11-10)

Frodo and Legolas: their arrow slots squeeze the Backpack text into 3 scrolling lines, so the page panel also shows
the item menu (substate 1: Equip/Unequip, Discard, Carve Rune if [0x030041B8], Move Item for backpack cursors 8-15,
Trade if [0x03004144] & 0x20; option under the cursor [0x030041BC]) and "Are you sure?" (substate 3, Yes/No
[0x030041C4]). Page-only change.

## Rich lighting (Play Room v150, 2026-11-10)

Graphics upgrade step 1 (Jordan asked for a big upgrade to textures, detail and colouring). After the Sharp HD
passes, `makeSharpHD` now runs two small game-size passes (bright warm pixels blurred into a glow map; the alpha
keeps a wide luma blur) and replaces the final blit with a lighting pass at screen size: relief light from the top
left, deeper shadows from wide local contrast, split-tone grade, saturation, soft sun gradient, fog, glow (screen
blend) and vignette. Values come from a look per level group (same groups as the Siege picker; menus use a soft
look). The page reads state 0x030041B0 and level 0x030041F8 every 0.4 s and eases toward the new look.
Off switch: "Rich lighting" button on the setup screen, or G while playing (localStorage `rotk-light=0`).
Sources: `playroom/rich-lighting-*.js`; `rich-lighting-patch.py <page> <out>` applies them to the page.
Before/after: project files `screenshots/rich-lighting-v150.png`.

### Water (v151, 2026-11-10)
Jordan said the water still looked bad (Frodo's Morgul levels). The lighting pass now finds water pixels (green and blue well above red; sky and grass excluded), blurs away the tiled zigzag, wobbles it (refraction), gives it a deeper body colour per look (`WaterCol`), moving light bands, round sparkles and shore foam. Shader source: `playroom/rich-lighting-final.glsl`. Picture: `screenshots/water-v151.png`.

### v152 (2026-11-10)
Jordan: water motion flickered, white rim round enemies, cloud reflections looked like stone, walls picked up water, menus not upgraded. Water is now still (no wobble, bands, sparkles or foam), stricter water colour test, pale reflections count as water only when surrounded by water, stronger blur. Every non-play screen (title, loading, pause, backpack, stats) uses the full menu look.

### v153: cloud reflections removed from water (Jordan). Pale teal pixels (green above red, so grey stone is left alone) with water all round are painted over with the average of the nearby non-pale water.

## HD-2D lighting (Graphics phase 1)

A second lighting pass on the Play Room page, off unless the player turns it on. It keeps the crisp pixels and adds form light, coloured lamps, soft shadow, fog, a few motes, bloom and a cool-shadow / warm-light grade. The native PC window does not run this chain (that is a later phase). The camera is unchanged.

Apply it to a page that already has the v162 patches (rich lighting, moods, day/night, aura), and after `alive.py` if that patch is on the page. It does not edit those scripts.

```
python3 recomp/playroom/hd2d-lighting.py in.html out.html
```

- Chip **HD-2D lighting** on the setup screen, or **H** while playing. `localStorage rotk-hd2d` is off when missing. **G** stays Rich lighting. While this is off the pass is not compiled and the picture path is the one the page already had, including the plain-pixel fallback when the frame rate stays under 40/s.
- The pass reads the picture the page just drew (Sharp HD, then rich lighting when that is on) and the ungraded 1x buffer for height. Fetches inside branches use `textureLod` / `texelFetch`.
- **Normals.** `NMode` 0 derives a normal from a wide luma neighbourhood and flattens it where the picture is flat, including under the HUD row (`HudY`, the bottom 34 rows). `NMode` 1 samples `window.__hd2dNormalImage` (image or canvas, same framing as the picture, RGB packed 0.5 = 0, alpha = coverage, author +Y up). `NMode` 2 samples `skin/normals.png` with `skin/map.json`, same 36 px cell, 2 px pad and FNV-1a key as the skin atlas. Tags are read only when the skin hook is already on (`rotk-skin` and `rotk_skin`); blended and faded pixels fall back to luma. `window.__hd2dDbg = 1` shows the normal.
- **Lights.** Up to 12. Detected from bright saturated pixels that differ from their neighbours (torches, spells, lava), plus Gandalf at the same object position as the aura (hero id 3, x/y at +0xAE/+0xB2). `window.__hd2dLights` adds more `{x, y, r, k, col}` in cropped-picture pixels, origin top-left. `window.__hd2dParts` replaces the built-in motes (embers inside lamps, dust in the upper air) with the same shape, up to 8.
- **Shadows and fog.** A soft key-light shadow, sharper on a colour edge, and a contact blob under Gandalf. If Living light is also running (`ShadeK` on the current look), this shadow term is halved so the two do not stack. Fog is thicker toward the top of the playfield and in dark pixels, thinner on the hero and on emissive pixels. Menus keep a light grade so the UI stays readable.
- Sources: `playroom/hd2d-lighting.glsl`, `playroom/hd2d-lighting.js`, `playroom/hd2d-lighting.py`.

## Crisp skin (Graphics phase 2)

Nearest pixel display for the Play Room, off unless the player turns it on. ScaleFX stays the picture while this is off, including the 3x linear skin pass when that patch is on the page. While it is on, ScaleFX does not run. The picture is an integer nearest scale of the game pixels, 4x by default, and a `skin/atlas.png` pack is drawn into that buffer with nearest filtering (one authored texel per output pixel, not a 4x atlas squeezed through ScaleFX). That buffer is what rich lighting and HD-2D then light. `skin/normals.png` is sampled by the HD-2D pass while this path has the skin hook on.

Apply it after `hd2d-lighting.py` when that patch is on the page, and after `tools/skin/patch_skin.py` when that patch is on the page.

```
python3 recomp/playroom/crisp-skin.py in.html out.html
```

- Chip **Crisp skin** on the setup screen, or **K** while playing. `localStorage rotk-crisp` is off when missing. **G** and **H** are unchanged. `localStorage rotk-crisp-scale=3` uses a 3x nearest buffer instead of 4x.
- Without a pack, the game's own pixels are scaled nearest, so the picture stays hard pixels under the lights. With `skin/atlas.png` and `skin/map.json` (same 36 px cell and FNV-1a key as the skin tools), matched tiles are the 4x art and the rest stay the game pixels. The old skin chip is not required.
- The native PC window does not run this chain.
- Sources: `playroom/crisp-skin.glsl`, `playroom/crisp-skin.js`, `playroom/crisp-skin.py`.

## Crisp 2x redraws (Graphics phase 3)

Hand-drawn 2x tiles for the crisp-skin atlas. Each game tile is authored at 16x16 (two pixels for one GBA pixel), snapped to at most 15 RGB555 colours, then nearest-doubled into the 32x32 cell (36 with the 2 px pad). Nothing is filtered or upscaled by a model. The pack is not loaded until Crisp skin is on and the files sit in the Play Room's `skin/` folder.

There are no extracted character sheets on main. `tools/colorplan/` only reads local captures, and those files are left alone. The shipped figure is an original stand-in (a wayfarer), and every key starts with `standin:` so it cannot replace a real tile.

```
python3 -m tools.redraw.standin skin/standin
```

That writes `skin/standin/atlas.png`, `map.json`, `normals.png`, and `catalog.json`. To use a real sheet later: draw or export each tile at 16x16, set its key to the FNV-1a string `tools/skin/cut.py` writes (`%08x%08x%d` of tile bytes, palette-bank bytes, 8bpp flag), and pack with `tools/redraw/pack.py`. Copy `atlas.png`, `map.json`, and `normals.png` to the page's `skin/` directory. Crisp skin still has to be turned on.

- Sources: `tools/redraw/`.

## Extra frames (Graphics phase 4)

In-between frames on the same atlas. The wayfarer stand-in has an 8-frame walk and an 8-frame swing: four poses each, and a smear frame after every pose (a one-pixel outline streak, same palette, no blur). The page patch is off unless the player turns it on.

The game's anim stepper (`0x080022E4`) leaves the shown frame in object +0x22 and counts +0x20 down. While Extra frames is on, the second half of that count swaps the tile's atlas cell for the smear cell named in `skin/anim.json`. The first half keeps the cell the tile key already selected. Stand-in keys still do not match the game, so nothing changes until those keys are the real FNV keys of each game frame.

```
python3 -m tools.redraw.standin skin/standin
python3 recomp/playroom/anim-frames.py in.html out.html
```

Copy `anim.json` with the atlas into the page's `skin/` folder. Chip **Extra frames**, or **J** while playing. `localStorage rotk-anim` is off when missing. **G**, **H**, and **K** are unchanged.

- Sources: `playroom/anim-frames.js`, `playroom/anim-frames.py`, `tools/redraw/cycles.py`.

## v155 Skin (test) hook (graphics thread, 2026-11-10)
- `recomp/gbarecomp-skin.patch` (gba_ppu.cpp + host_window_web.cpp): when `rotk_skin(1)` is on, the wide renderer writes one
  u32 tag per output pixel: bits 0-11 VRAM tile slot (addr/32), 12-15 palette bank, 16 8bpp, 17-19 texel x, 20-22 texel y,
  23 hflip, 24 vflip, 25 OBJ, 26 alpha-blended, 27 brightness fade, 31 valid. `rotk_skin_slot(i)` = tags of video slot i.
  Affine BG/OBJ are not tagged. Off by default, no cost when off.
- `recomp/web/shim-skin.cpp` = shim.cpp + `rotk_vram()` / `rotk_pal()` (read-only).
- runtime.cpp also needs `extern "C" EMSCRIPTEN_KEEPALIVE void rotk_bg_tick() { if (g_web_iter) web_single_tick(); }`
  next to web_single_run (it was missing from the gbarecomp tree).
- Page: `tools/skin/patch_skin.py in.html out.html` adds the skin pass after ScaleFX (atlas skin/atlas.png + skin/map.json,
  key = FNV-1a hex of tile bytes + palette bank bytes + 8bpp flag). Chip "Skin (test)" on the setup screen, localStorage rotk-skin.
- Pack: `tools/skin/capture.js <level>` (headless, saves frames + tags + VRAM + palette), Real-ESRGAN anime 6B 4x
  (tools/skin_upscale.py), then `tools/skin/cut.py OUT capdirs...` keeps only fully visible, unblended tile instances.
  Helm's Deep (level 46) pack: 1036 tiles from 60 screens. Tested headless: tags rebuild the frame exactly (72960/72960 pixels).
