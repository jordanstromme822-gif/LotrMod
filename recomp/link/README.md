# P2 helper: two linked games in the Wide engine

Jordan (2026-11-08): "Create a P2 button next to auto. The button allows you to choose one of the
currently non selected heroes from the load menu. After selecting, P2 updates its save when you save.
It acts like the auto except P2 stays on Auto's screen." Picture: Wide 60 fps.

## How it works

- `link_main.cpp` is the PC/web main with a link mode (`ROTK_LINK=1`). It runs two copies of the
  game in a `gbarecomp::GbaMultiplayerSession` joined by the link cable, shows only game 0 (P1) with
  the wide view and in-between pictures, and takes P2's buttons from the page (`rotk_link_p2`).
- Exports for the page: `rotk_link_on`, `rotk_link_frames`, `rotk_link_iwram(i)`, `rotk_link_ewram(i)`,
  `rotk_link_save(i, out)` (8 KB EEPROM copy since v124, returns 1 when changed), `rotk_link_level(82)`
  (forces Moria on both games while the level is still pending after Choose Your Path).
- The session needs every guest PC to have native code, so:
  - the Cult-of-GBA BIOS is recompiled too (`cobios.toml`, generated into the runtime with
    `GBARECOMP_GENERATED_BIOS_DIR`),
  - `game-link.toml` adds the misses found in link play plus every Thumb function-pointer target in the
    ROM (aligned word `0x08xxxxx1` pointing at a `PUSH {..,LR}`),
  - `mixer_hook.cpp` runs the game's self-modifying IWRAM sound mixer (0x03000B38) and IRQ helper
    (0x03000004) natively,
  - any remaining miss is bridged through the interpreter and printed once
    (`[gbarecomp:link] bridged <pc>`); add it to `game-link.toml`.
- `gbarecomp-link.patch`: runtime changes (session hooks on game 0 only, bridging, slice lookahead,
  `runtime_web_run_frames` for the web).
- The web build needs `-fwasm-exceptions` for the runtime libraries, `link_main`, `mixer_hook`, the shim
  and the final link: the session yields with a C++ exception.

## Page side (Play Room `wideP2`)

- The P2 button sits next to Auto. Solo: lists the saved heroes other than the loaded slot
  (`0x03005834`); picking one stores `{p1, p2, moria}` in sessionStorage `rotk-p2` and reloads.
- Start: both games go Title → Multiplayer → Load Game, each cursor (`0x030041BC`) moves to its slot,
  then P1 presses A three times on Choose Your Path.
- Saved-games file: slot k at `0x40 + 0x70 k`, 8-byte blocks with their bytes reversed (hero =
  byte `0x62 >> 4`, level = byte `0x5B` + 1). The page keeps both games' EEPROM copies and writes P1's
  file with slot `p2` taken from P2's game.
- Pause: state 16; `0x030041C0` = 2 means "waiting for the other player". When P1 picks Save Game
  (P1 state 9), P2 saves its own slot (A into the save screen, wait 150 frames, A only if the cursor is
  on P2's slot, Left + A for Yes, A, B). When P1 is waiting, P2 presses B.
- In a level P2 fights enemies and picks up herbs and food within 100 x 62 px of P1, and otherwise
  walks back next to P1. It never equips, discards, sells or uses the Forge.

## Speed notes (2026-11-08, v97)

Profile of the browser build in Moria (2 games, wide view): about 20% in `runtime_should_yield`
(called before every guest instruction of both games), about 14% drawing P1's wide picture,
about 15% in the session loop and device ticking. Compiling the game code at -O2 instead of -O1,
and skipping P2's sound mixing (`g_link_quiet_bus` in mixer_hook.cpp), made no measurable
difference, so v97 still ships the -O1 build without the quiet mixer.

## v102 (2026-11-08): P2 plays more like a person

- Smooth walking: re-plans about 7 times a second and heads for the furthest point of its route it can see,
  steering diagonally only when the smaller offset is a real part of the move.
- Reacts to a newly seen enemy 0.15-0.3 s later; small random pause between swings.
- Stands beside P1; when P1 is on an enemy, P2 comes at it from the other side.
- Casts learned skills on elites and groups (same as Auto; writes go to both games with `w8both`).
- Backs off behind P1 for up to 4 s when HP < 30% with enemies near (note "P2 is low on health!").
- Picks up gear only when it is an upgrade for P2 (hero, level, better than worn and packed), and wears
  backpack upgrades through its own Backpack menu (state 10 in P2's game only; P1 keeps playing). The
  menu macro is state-driven (Start until state 10, A until sub 1, A); fixed timings missed presses.
- Engine: `multiplayer-slice-speed.patch` (ROM fast path for the opcode fetch, direct-mapped ARM decode
  cache instead of a hash map in `multiplayer_slice_safe`), about 10% faster 2-player in the browser.
- A narrower picture (288 instead of 320) gave no measurable gain, so it was not shipped; 240 was about 13%
  faster.

## v121 (2026-11-08): Legolas plays like a ranger

Jordan: "Legolas P2 doesn't play the way a ranger should". When P2's hero is Legolas (hero id 1 at hero + 0x19F):
- Keeps bow distance: it plans to a shooting spot 56-72 px along the target's row, 52 px on its column or 46 px on a
  diagonal, with a clear line to it, preferring spots near P2 and on P1's side of the target (P1 stays the front line).
- Shoots only when lined up (row within 7 px, column within 7 px, or diagonal) with a clear line, after a 1-frame turn
  toward the target; skills on elites and on groups of 3 or more near the target.
- Kites: an enemy within 34 px makes it step away (toward P1's side, sideways if blocked); it swings in melee only
  when there is no room to back off.
- Targets the enemies near P1 first, then elites, then the nearest. Follows P1 a little further back (34 px) when
  there is nothing to shoot.

## v121: Orc Head hooks compiled natively

The 2-player engine used to run the hook code (tools/orcslots) through the runtime's interpreter, like the solo
engines still do. Nested bridges crashed it: first the Orc Head link message (type 4), whose receive case jumps back
into the game's receive loop (0x0803FDAC), then, in long fights, a call to 0x00000008 deep inside nested bridges
(entry depth 7). Both showed as a dispatch miss at 0x00000008 and also happened in v120.
Now every hook entry is compiled natively: the end of `game-link.toml` lists them as `extra_func`
(written by `orcslots/linkfuncs.py` from `tools/orcslots/orcslots.sym`). `recv4` sits at 0x0807F000, never calls
anything and keeps its own literals; it only stores the heads, and `gp_hook` puts them on next tick.
To regenerate after a hook change: build `tools/orcslots`, run `linkfuncs.py`, write `orcslots.bin` at 0x7F000 into
the ROM you generate from (the toml's sha1 must match that ROM), generate, re-apply the three noquickskill edits
(shards 002, 003, 007) and run `orcslots/genpatch.py`; compile `dispatch_table.cpp` and `symbol_map.cpp` too.

## 2-player speed-up (2026-11-11)

Jordan: 2-player games lag on the iPhone in big fights. Measured natively with a headless big fight (both games
booted into Hornburg Valley, level 47, with an extra set of the level's enemies from the test-only spawn ROM,
`tools/engine/build_spawntest.py` with its request block moved to EWRAM 0x0203FD80 because 0x0203FF00 holds the Orc
Head slots), profiled with callgrind:

- P2's picture was already not drawn (`set_rasterization_enabled(false)` on the hidden game).
- P1's wide picture: about 40% of the time. Handover check before every guest instruction (`runtime_should_yield` +
  `multiplayer_slice_safe`): about 23%. Byte checks on the game's code in IWRAM (`runtime_native_ram_instruction_matches`):
  about 13%. Nothing ran in the interpreter.

Changes (`link-speed.patch` on top of the runtime patches listed in `build-web.sh`, plus `link_main.cpp`):

1. **Repeat frames are not drawn again** (`GbaPpu::render_scanline`, `g_ppu_repeat_skip`). The game draws a new
   picture at most every other VBlank, and far less often in big fights. A frame whose registers (per line), palette,
   OAM, BG VRAM and the OBJ tiles that enabled OAM entries use all match the frame that was last drawn keeps that
   frame's pixels. The game streams the next animation frames into free OBJ tile slots while a picture is showing, so
   only tiles in use count. VRAM, OAM and palette are checked again after the last line; if they changed during a
   skipped frame, the frame is drawn from the end-of-frame memory. The wide margins come from the level's block map,
   so `rotk_view::frame` passes a signature of the view and block maps (`g_ppu_view_sig`). `ROTK_REPEAT_SKIP=0` turns it
   off. Over 2,300 test frames, 5 differed from a full redraw by a few HUD pixels for one frame (a HUD update in the
   middle of a frame shown one frame early).
2. **Inline IWRAM code checks**: the runtime and the game code are built with `GBARECOMP_NATIVE_RAM_CODE_VIEWS`
   (an upstream option), so each check is a load and compare instead of two calls through a function pointer.
3. **Cheaper handover check**: `multiplayer_slice_safe` keeps a 16-byte verdict per opcode instead of a heap `Instr`,
   decoding out of line; `runtime_should_yield` and `runtime_tick` have an inline fast path for an instruction inside
   a running slice and keep the rest out of line.

Every change leaves the games' memory exactly as before (pictures with the skip off are identical frame for frame),
so online games still hash the same; both players still need the same engine build.

Headless test (native `link_main`, not the web build): `ROTK_LINK_AUTO=p1slot,p2slot` boots both games like the page,
then a fight bot keeps both heroes at full HP, attacks and walks a square, and prints `[speed]` lines (ms per frame,
object count, frames skipped/drawn/redrawn) every 300 frames. `ROTK_LINK_POKES="after:addr:value;..."` writes RAM in
both games after the level starts. Under valgrind the frames from `ROTK_PROF_FROM` for `ROTK_PROF_N` are profiled.

## ALU yield fast path (2026-11-12)

`link-alu-yield.patch` (apply to gbarecomp) lets plain ALU/multiply instructions
skip the full `runtime_should_yield()` check while the session slice deadline
is still ahead (`runtime_should_yield_alu`, cached deadline reset on every
slice/dispatch boundary). Game state is identical frame for frame (`hash=` in
the `[speed]` line). Native 2-player fight: 12.4-12.6 -> 10.6-11.1 ms/frame
(~12-14%); browser at 3x CPU throttle: +6-9% engine frames/s.
Regenerate the link code with the patched `gba_recompile` after applying it.

## P2 inside one game: stand-in partner (prototype, 2026-11-13)

Jordan: nobody links any more, P2 just joins. In a level the two games only swap one 12-byte message per
game tick (every 2 frames), after a fixed handshake (slave sends beef c0de c0de babe babe):

- word 0: message type (0x13 = buttons) | sequence << 8. P2's sequence is always the master's minus 1.
- word 1: check word = -(byte sum of the other words + shared session state). So P2's check word =
  master check word + bytesum(master) - bytesum(P2). The master's packet in flight is at IWRAM 0x03006D14.
- word 2: buttons, 0xFC00 | pressed bits (~KEYINPUT, built at 0x0803FEFC).
- word 3: sender's hero position, low bytes of obj+0xAE (x) and obj+0xB2 (y); hero obj ptr at
  0x03003C00 + 0x1AC * player.
- other message types (events, e.g. type 6) carry the same payload on both games.

`one-game-partner.patch` (gbarecomp) adds `gba::g_link_virtual_word` (a hook that supplies port 1's word at
each transfer), `gba::g_link_virtual1` (port 1 follows port 0's clock) and `gbarecomp::g_session_skip_mask`
(skip a machine's CPU and devices). link_main: `ROTK_VP=check` compares the stand-in's words with the real
second game; `ROTK_VP_AT=<frame>` switches the second game off at that frame and the stand-in takes over.
Headless Hornburg fight (spawn test): game keeps running, P2 keeps moving and fighting; 6.7-8.3 ->
3.9-5.0 ms/frame (~40% less). Boot, menus and level start still need the real second game (type 0x14/0x15
messages carry P2's own data), and P2's own Backpack menu runs in P2's game.
