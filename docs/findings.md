# Findings: how the game is built

ROM: 16 MB, game code `BLRE`, maker `69` (Electronic Arts), developed by Griptonite (Amaze
Entertainment). Save type EEPROM (`EEPROM_V122`). SHA-1 of the copy we studied:
`ec3d126d37ea6e2ad7030d8a99cf87c6e46c03fd`.

Addresses below are ROM file offsets unless they start with `0x02` (EWRAM), `0x03` (IWRAM)
or `0x08` (ROM as the CPU sees it).

## Game structure

- Title menu: New Game, Load Game, Multiplayer, Options, GCN Link, Bonus Maps.
- Heroes in the text: Frodo, Legolas, Aragorn, Gandalf, Gimli, Sam (plus a seventh slot).
  At New Game, Legolas, Aragorn and Gandalf can be picked.
- It is a Diablo-style action RPG: Experience, Attribute Points, Skill Points, items with
  affixes (for example "+5 Courage", "Gemfinder"), rune carving, gems, shops.
- Attributes: Strength, Accuracy, Health, Defense, Courage.

## Text

- All text is Huffman-compressed. The language table at `0x289A10` points to 5 banks
  (English, French, German, Italian, Spanish). English bank starts at `0x7500C`.
- Each bank holds 2,021 strings. Decoder: `0x080299A0`. Format is documented in
  `tools/text.py`, which dumps everything.
- Editing text: re-encode the strings (new Huffman tree if new characters are needed),
  write the new bank to free space and point the language table at it. Free space inside
  the 16 MB ROM is small (about 13 KB at `0xFFCB89`), so new text goes in the expanded area
  (see below). We're keeping English only, so the 4 other language banks (~170 KB from
  `0x7EE28`) are also free to reuse once every language entry points at English.

## 32 MB expansion

- `tools/expand.py` pads the ROM to 32 MB with `0xFF`. New space: ROM offsets
  `0x1000000`–`0x1FFFFFF`, CPU addresses `0x09000000`–`0x09FFFFFF`.
- Tested in mGBA: boots, saves to a slot ("Game saved successfully"), and after a reset the
  save shows up in Load Game.
- Caveat: the save code (`0x0804DDEC` and its callers, which build the address with
  `movs rX, #0xD0; lsls rX, #0x14`) talks to EEPROM at `0x0D000000`. Real 32 MB carts only
  answer at `0x0DFFFF00`+, so flash carts and some emulators may not save until those call
  sites are patched. mGBA is fine.
- IPS can't address past 16 MB, so expanded mods are shared as BPS (`tools/bps.py`).

## Heroes and stats

- Player data lives in IWRAM at `0x03003C00`, one block of `0x1AC` bytes per player,
  indexed by player number. Base attributes are u16 values at offsets `+0x2A` to `+0x32`;
  `+0x2A` is Courage (confirmed). The game copies them to `+0xC6..+0xCE` and derives Hit
  Points and Spirit Points from them (`0x08025F74`).
- New Game starting attributes are hard-coded as `movs` immediates, one case per hero,
  around `0x25DAC`–`0x25EB0`. Aragorn's Courage byte is at `0x25DFA` (20).
  **Test mod:** setting it to 50 gave Courage 50, Hit Points 131 → 161 and Spirit Points
  102 → 222 on the character screen.
- Next: label every hero case and attribute, then find skill and item tables (their names
  are text IDs ~330–400 and the item list from ~576).

## Multiplayer

- Menu: Multi-Player → Trade or Play. Text only ever mentions "Player 1" and "Player 2",
  and Samwise unlocks through multiplayer.
- The link code (`0x08046400`–`0x08046C00`) uses the serial port in multi-player mode and
  polls all 4 hardware slots (`SIOMULTI0`–`3`), which is the normal library behaviour.
- Player data is already an array indexed by player number, which is the friendliest
  case for adding players. Still unknown: how many slots the arrays, sprite budget and
  sync code assume. That decides whether 4 players is possible (6 is not: the link cable
  tops out at 4).
- Next: run two emulator instances linked together to watch a real 2-player session.

## Tools

- `tools/run.c`: headless mGBA runner. Script commands: `<frames> <keys>`, `shot`, `ram`,
  `save`, `load`, `watch <addr> [span]` (prints the code address of every write).
- `tools/text.py`: text dumper.
- `tools/stats.py`: starting attribute editor (only verified entries).
- `tools/heroes.py`: all-heroes stat editor. 0x08025D6C(heroId, player) sets starting
  attributes via a jump table at 0x25D8C (ids 0 Frodo, 1 Legolas, 2 Aragorn, 3 Gandalf,
  4 Eowyn, 5 Gimli, 6 Sam, 7 Smeagol); every case resumes at 0x08025EB2. The tool expands
  to 32 MB, replaces the function start with a jump to a hook at 0x09000000, and the hook
  reads a table at ROM 0x1000100 (8 heroes x 16 bytes, u16 courage, defense, health,
  accuracy, strength). Struct offsets: courage +0x2A, defense +0x2C, health +0x2E,
  accuracy +0x30, strength +0x32. Verified in game for Aragorn and Legolas.
- `tools/ips.py`: make and apply IPS patches (16 MB only).
- `tools/bps.py`: make and apply BPS patches (any size).
- `tools/expand.py`: grow the ROM to 32 MB.

## Game states and frame rate

- State machine: setState(n) at 0x08033154 (and 0x08033170 with two args) writes n|0x80
  to 0x030041F0; the main loop applies it next frame. Seen states: 0x12 language select,
  2 copyright, 3 New Line/EA logos, 5 title, 8 main menu, 7 story cutscene slide, 1 gameplay.
- Boot: 0x080330E8 starts 0x12 on a fresh save, 2 when the save already has a language.
  `tools/quickboot.py` sends both routes to 5 (title), skipping copyright and logos.
- Story cutscenes: sequencer at 0x08045E78 re-enters state 7 per slide, then state 1.
  New game from the menu starts it at 0x080142BC (movs r0,#7).
- Frame rate: the main loop at 0x080315F6 runs one game tick every 2 vblanks (30 fps,
  movs r0,#2 at 0x080315EE). Changing it to 1 runs game logic twice as fast (text and
  movement speed up), so true 60 fps would need every speed and timer halved.

## Skills

- Active skills: per-hero tables of 6 skills x 6 bytes (hero order Frodo, Legolas, Aragorn,
  Gandalf, Eowyn, Gimli, Sam, Smeagol at 0x28758E, 0x2875FA, 0x28761E, 0x287642, 0x287666,
  0x28768A, 0x2875B2, 0x2875D6). Byte n = hero level needed for skill level n+1, 255 = never.
  Verified: Aragorn King's Command set to 1 shows "(level 1)" on the skill screen at level 1.
- Skill levels live in the player struct at +0x16A (signed byte per skill); hero id at +0x19F.
- Skill description text id = u16 table 0x082874A4[hero] + skill; passives = 0x1E3 + id.
- Skills page (state 0x0F, key handler 0x080416B4): A buys (0x08041F78), SELECT sets the B skill, GBA L (0x200) goes to the Backpack, R (0x100) to Stats, B/START close. Panel 0x030041C0 (1 actives, 2 passives), cursor 0x030041B8, passive id per cursor at 0x03006A10.
- Skill points: player + 0x19E. Hero level - 1: player + 0x19C. Each skill level costs 1 point.
- Actives: bought level + 0x16A + i, level in use + 0x170 + i (0x08045138 adds to both). New heroes get Herbal Healing (i = 5) at 1 for free; its unlock row is all 255, so it never goes higher.
- Passives: the hero's 9 ids at [player + 0x18]; bought level + 0x158 + slot, level in use + 0x161 + slot. Passive table 0x0806E3D4, 40 bytes per id: up to 3 bonuses of (type byte + 5 u16 per level), max level at +0x26. 0x0804539C(p, slot, +1/-1) adds or removes one level's bonuses. Loading a game copies bought -> in use and reapplies all bonuses (0x08042B6C).
- Keys per player (updated each game tick): new presses 0x03004080, held 0x03004088, new presses for menus 0x03004094 (+2 per player).
- `tools/skillrefund.py`: L + SELECT on the Skills page takes one bought level back and returns its point (passive bonuses removed, Herbal Healing's free level kept). In link play it sends the game's own skill message (0x21 / 0x22) with bit 7 set in the first byte and wraps those two cases, so both GBAs apply it. Tested single player (stats restored byte for byte, save and load) and with tools/link2 (both players refunding, both GBAs agree).
- Unmodified-game quirk seen while testing: after buying an active skill, saving and loading adds 1 melee and missile armor (Sweep 1: armor 2 -> 3). Not caused by the refund patch.

## Menus and input

- Game state byte at 0x030041B0 is 0x0A in the in-game Backpack/Skills/Stats menu, 5 on the title menu, 1 in gameplay.
- Menus move the cursor one step per fresh d-pad press (a 1-frame press is enough, holding does not repeat). With two directions held, the horizontal one wins.
- Boot copies code from ROM 0xCD5C to IWRAM 0x03002D30 (0x4DC bytes) and from ROM 0xE208 to 0x03002C30; the Play Room uses these to find IWRAM inside the emulator's memory.

## Reflections (flicker)

- Each OAM buffer (0x03004340, 0x03004B80) is two 1 KB images. Image 0 has every sprite plus the reflections (vflip, priority 3, drawn under BG2 water, which alpha-blends over OBJ: BLDCNT 0x1044, BLDALPHA 0x0808). Image 1 is image 0 minus the reflections.
- The vblank handler flips 0x03001F18 each frame and DMAs image (toggle), so reflections show on every other frame. `tools/noflicker.py` always picks image 0. In a 60-sample random walk of level 1, image 1 never had a sprite that image 0 lacked.

## Story cutscenes, dialogue, unlocks

- Story slides: table 0x0806F68C, 0x2C bytes per slide (+0x22 text id, +0x24 level arg, +0x25 type 4 first / 5 middle / 6 last, +0x26 next slide). Each slide is game state 7; after the last one the sequencer (0x08045E78) calls setState2(1, last.+0x24, [0x030041BC]). `tools/nocutscenes.py` hooks state 7's enter (0x0804587E) and queues that call straight away. Hook code lives in the freed Spanish text bank (0x9E400), so the patch also points every language at English. Special cases: slides 0x14 and 0x19 are single mid-level slides (the update at 0x08045C30 marks them last), and slides above 0x39 are the endings (0x3A is swapped per hero for 0x3C-0x44, plus 0x46); after an ending the game goes to the credits (setState(0x19), 0x08045B0A) and then the save screen, so the hook does the same. An earlier version sent endings back into a level.
- In-level dialogue: everything opens through 0x0801AD9C(textId), which switches to game state 0x11 until A. Script command 0x08018454 has a multiplayer path that skips the box and runs the follow-up (0x0800C4AC). `tools/nodialogue.py` makes 0x0801AD9C return and always takes the multiplayer path.
- Heroes: the select screen is a fixed ring of 6 (Frodo, Legolas, Aragorn, Gandalf, Eowyn, Gimli), all open from a fresh save. Sam (6) and Smeagol (7) have stats and skills but no select entry or description text.
- Bonus Maps: main menu item 5 goes to the slot screen in mode 4, then "Choose your path" (state 0x18). Path table 0x08050634 (0x1C bytes, unlock mask at +0x18: 0x10000000, 4, 8, 2) is checked against save progress bits at 0x0300581C (header template in ROM at 0x0806E0C4). `tools/unlockpaths.py` removes the four checks.
- Sam and Smeagol are the game's own unlockable heroes: a save slot's "Select Hero" picker (0x080308F4, used for Bonus Maps) cycles heroes 0-7 and skips Sam unless progress bit 0x1 and Smeagol unless bit 0x4000 is set. `tools/unlockheroes.py` removes both checks. Tested: Smeagol plays Moria from Bonus Maps.

## Save slot screen (Load Game / Save)

- Game state 9. State table at `0x0806C828` holds (init, update, draw) per state; state 9 is
  init `0x080305C4`, update `0x080306EC`, draw `0x08031368`. Substate at `0x030041C0`
  (0 list, 1/2 prompts, 3 result message), slot cursor at `0x030041BC`.
- New presses come from `0x03004094` (written by the input routine at `0x08029D00` from KEYINPUT).
  The update checks d-pad, then A (`0x08030970`), then R (`0x080313B8`, opens
  "Delete this saved game?"), then B/Select (`0x08030C00`).
- The prompt cursor starts on No; Yes erases the slot through `0x08030F08`.
- `tools/nodelete.py` removes the R call at `0x080307F0`, skips drawing the "Delete" word
  (bl at `0x08030CFA`) and moves the R button sprite (x set at `0x08031108`) off screen.
- Slot headers live at 0x03005630 + slot*0x70. Load is 0x08031490, save/erase is 0x08030F08(1/0); both store the slot in 0x03005834 ("last slot", used to place the cursor). Save mode is [0x030041B4] = 1 (pause menu) or 3 (after the credits).
- `tools/nodupe.py` blocks the Ranger Hollow dupe (save one game into several slots, empty each copy into the shared Hollow): a lock byte at 0x0203FFF0 (unused EWRAM) holds the session's slot, set on load or save, cleared by the title screen, and A on any other slot in save mode only plays the cancel sound.
- `tools/run`: in this libmgba build key bit 8 is L and bit 9 is R (the script names now match).

## Items and equipment

- Hero inventory is 32-bit item words: bits 0-3 category (0xF = empty), bits 8-15 index, upper bits prefix/suffix. Equipment slots at hero + 0x3C (armor), + 0x40 (weapon), + 0x44 (shield), ... + 0x58; the backpack grid starts at hero + 0x5C.
- Category table at 0x08068F50, 0x28 bytes each (+0x20 pointer list, +0x24 count): 0 knives, 1 swords, 2 two-handed swords, 3 axes, 4 clubs, 5 staves, 6 bows, 7 arrows, 8 armor, 9 shields, 10 amulets, 11 capes, 12 gloves, 13 wrappings, 14 uniques. Base item entries are 12 bytes (name text id, then (stat, value) pairs, 0x5A = none).
- Correction: in the item word, bits 0-3 are the category and bits 8-15 the index (so `tools/run` peek shows a halfword like `04fd` = category 13, item 4, Boots). Equipment slots, in order from hero + 0x3C: body armor, weapon, shield, helmet, cape, gloves, footwear (+0x54), amulet.
- Each category's +0x20 list holds 8 bytes per item. Bits 26-31 of the first word are the heroes who may equip it (26 Frodo, 27 Legolas, 28 Aragorn, 29 Gandalf, 30 Eowyn, 31 Gimli); bits 18-25 pick the slot (18 body, 19 main hand, 20 off hand, 21 helmet, 22 cape, 23 gloves, 24 footwear, 25 amulet). The equip menu checks level first ("not high enough level"), then this mask ("This hero cannot equip this item!"). Frodo is left out of all footwear (category 13) and the six heaviest armors (category 8, items 18-23). `tools/frodogear.py` adds him; his Backpack screen then shows a footwear box at the bottom left, and the item's stats apply (Boots: Melee Armor at hero + 0xBE 4 -> 8). Tested in the core with Jordan's save.
- Equip/unequip apply stat deltas through 0x0802DDC4(category, stat, hero, delta); max melee damage is hero + 0xA4. `tools/nostack.py` fixes the half-delta special case for two-handed swords that let damage stack.

## Ground pickups (gems)

- Items on the ground are entities with update 0x0802F130 (+0x14) and touch callback 0x0802F580 (+0x18). Item type byte at +0x60 (name = text 568 + type: 13 A Gem, 14 A Pile of Gems, 15 Fruit, 16 Mushrooms, 17/18 Kingsfoil, ...), item word at +0x88, state +0x63 (1 = taken), lifetime +0x84 (1800 ticks), spawn delay +0xF0.
- The update sets item + 0x8C + player when that player's hero is within 15 pixels and no other item holds the player's HUD label (0x03003F70 + 0x7C * player + 0x70). The IWRAM collision loop calls the touch callback while hero and item overlap (r0 = item, r1 = hero); it picks up only on a fresh R press (0x03004080 + 2 * player, bit 0x100) with that flag set. Gems add byte1 + byte2 + byte3 of the item word to player + 0x184 (u16).
- `tools/autogems.py` (Jordan, 2026-11-06): gems are taken on touch, no R. Hook at 0x0802F59E calls 0x0809EC80, which for types 13/14 only checks that the toucher is the player's own hero ([0x03003C00 + 0x1AC * player]); other items keep the R + label rule. Tested: walking onto a gem and a pile (1 + 7) gave 8 gems with no buttons; the unpatched game gave 0 until R; herbs still need R.

## Orc Head slots (Backpack screen, state 0x0A)

- State table at 0x0806C828, 12 bytes per state (enter, update, exit). Backpack: enter 0x0802A4DC, update 0x0802A798, exit 0x0802E874. UI struct pointer at [0x03001FE0]: cursor byte +0x62 (0-7 equipment, 8-15 backpack grid, 16-19 top icons), cursor sprite position +0xAC / +0xB0 (x << 16, y << 16), position table 0x08062AA4 (8 bytes per cursor). Substate [0x030041C0]: 0 idle, 1 item menu, 2 closing it, 4 Carve Rune, 6 Move Item.
- D-pad movement is 0x0802C928; every substate-0 path ends at 0x0802CC60 with the new cursor in r4, then 0x0802E600(cursor) sets the cursor picture and 0x0802CFFC(cursor) draws the description. A in substate 0 is handled from 0x0802A840; cursors above 15 already give the "can't" sound (0x0802AB9C, sound 5).
- Item pictures in the grid are sprite objects: 0x0802E1E0(slot) makes one, 0x0802C08C(slot, player) removes an item and its picture (discard). The game adds OAM entries through 0x08036540(index, attrs) with the count at 0x03004220 and hides the rest in 0x080366A4.
- Text is on BG1 (screenblock 0x1E, written straight to VRAM): drawText 0x0801D6D0(tile, x, y, width, string, 0) returns the next free tile, 0x08012660(1, 15, 10, 15, 10, 0) clears the description box, 0x0801D5C0(0, color, 0) sets the color. Strings are plain bytes. Item box frames are BG0 (screenblock 0x1F) tiles; the grid rows are tile rows 4-6 and 7-9, columns 15-29.
- Keepsakes ("Keep in backpack to use", list word bit 16) add their stats from the backpack through 0x0802DB90(item, slot, player, remove); its keepsake path (0x0802DBE0) skips heroes whose id byte (+0x19F) is 7 (Smeagol) and checks the hero mask and level. 0x0802ACE8 (pick up) and 0x0802C08C (drop) call it. Loading a game and levelling up reset the attributes (0x08025F74) and add every item again (0x0802AC24, called at 0x08026014).
- Save slot header (0x70 bytes, packer 0x0803C6CC, unpacker 0x0803C294, also used for the other player's hero in link play): running both in Unicorn with every input bit set shows bits 5-7 of byte 0x4B are never written or read; everything else is used.
- `tools/orcslots.py` (Jordan, 2026-11-08): 4 slots under the grid, one Orc Head (unique item 23, word 0xFFFF17FE) each, +1 Courage per head only from there. Count per player at EWRAM 0x0203FFE0 (saved in header 0x4B bits 5-7, cleared by the title screen); the backpack keepsake path returns "no bonus" for Orc Heads in slots 0-15 and our slots call it with slot 16; the text layer is shown from a copy (screenblock 0x1B) with rows 10-17 moved to 13-18 (one empty row dropped), except in Carve Rune. Text 418 (the Orc Head description) re-encoded at 0x9FC00. Code is C in tools/orcslots/, at 0x9F000. Slots are drawn dark red (grid box tiles shown with BG palette 6, a red copy of palette 2) with a faded Orc Head (OBJ palette 11) in empty ones; both palettes are unused on this screen. Locked in 2-player games (A gives the "can't" sound); the saved count still applies there.

## Free space map (Spanish text bank, English only)

- 0x9E400-0x9E46F: story-cutscene hook (tools/nocutscenes.py).
- 0x9E880-0x9E8D5 dialogue allow hooks, 0x9E900-0x9E90F allow bitmap (tools/sidequestdialogue.py).
- 0x9E940-0x9E963: level-setup flag hooks (tools/fastloads.py).
- 0x9E600-0x9E68B: hero stats routine, 0x9E6E0 marker, 0x9E700-0x9E77F hero table (tools/heroes.py).
  The hero hook used to live in the 32 MB expansion; it moved here so the modded game stays 16 MB
  (half the memory on phones, and saves use the normal EEPROM address on any emulator).
- 0x9E800-0x9E80B: Options label helper (tools/nolanguage.py).
- 0x9EC80-0x9ECCF: gem auto pickup (tools/autogems.py).
- 0x9E820-0x9E877: save slot lock (tools/nodupe.py).
- 0x9EA00-0x9EC47: skill point refund (tools/skillrefund.py).
- 0x9F000-0x9F9BF: Orc Head slots code, Orc Head picture and slot palettes; 0x9FC00-0x9FC3F: its re-encoded description (tools/orcslots.py).

## Testing

- `tools/run` script commands: frames + keys (L and R now match the GBA's own bits: L = 0x200, R = 0x100; they were swapped before), `shot`, `peek`, `poke <addr> <u32>`, `watch`, `break`, `save`/`load` states.
- Story-slide test: from gameplay, poke the pending state block 0x030041F0 = {0x87, 0, slide, level}
  (what script command 0x1B, 0x08018670, does) and check the game ends in state 1, or 0x19 then 9 for endings.

## Options menu (game state 6)

- Rows: Music Volume, SFX Volume, Quick Skill Select, Auto Healing, Fast Discard, Difficulty, Language Select, Credits. Cursor is [0x030041B8]; row i is drawn by 0x08036AE8 with text 0x39 + i at y = 0x20 + 16*i. Difficulty (row 5) is skipped when Options is opened from the title screen.
- Working copy of the settings is 0x03002080 (+0 music, +1 sfx, +2 quick skill, +3 auto heal, ...). The saved copy is the bit field at 0x03005820 (0x030057F0 + 0x30): bit 3 quick skill, bit 4 auto heal. Leaving Options calls 0x080265C0, which copies them into each hero's flags at player + 0x19A (bit 1 quick skill, bit 0 auto heal).
- Quick Skill Select: with it on, the Skills page (state 0xF) shows A, B and R badges on three skills, and in play holding L and pressing A, B or R uses that skill (player + 0x191.. holds the slot map). Verified in the core: L+A fires the A skill.
- `tools/nolanguage.py` removes Language Select: 7 rows, Credits in row 6, label helper at 0x0809E800.
- `tools/noquickskill.py` (after nolanguage) hides Quick Skill Select: row 2 not drawn, rows below move up, cursor skips it (helpers 0x0809ED00). Skill Spirit cost: the hero's skill table pointer at player + 0x1C (ROM, 40 bytes per skill), cost u16 at +4; 0x080430E8 checks it before a Quick Skill.

## Side-quest dialogue

`tools/sidequestdialogue.py` replaces `tools/nodialogue.py`: story dialogue stays skipped, but dialogue ids 21, 28-30, 33-35, 37, 41 and 48-53 (table 0x08050CE0, the side quests that give a reward) still open their box. Hook 1 (bl at 0x0801AD9E inside 0x0801AD9C) returns to the caller for any id not in the bitmap; hook 2 (bl at 0x0801846E in script command 0x08018454) sends multiplayer and non-allowed ids down the existing skip path at 0x08018484. Checked in a Unicorn harness: allowed ids reach setState(0x11), others reach the follow-up action 0x0800C4AC, multiplayer always skips, stack balanced.

## Fades and level loads

- All screen fades are loops of BLDY (0x04000054) steps with two vblank waits (0x0802A398) per step: 0x0803D354, 0x0803D4B2, 0x0803E07C, 0x0803E15C, 0x0803E1E0, 0x0803E348, 0x0803E388, 0x0803E414, 0x0803E658. Loading a save measured 28 frames fade out, about 36 frames of black (state 1 init 0x08031634 doing real work, one vblank wait), 32 frames fade in (0x0803E148, called at 0x08031DBA).
- `tools/fastloads.py` drops the second wait (fades take 16 frames) and sets EWRAM 0x0203FFF1 during state 1 setup (set at 0x0803163E, cleared at 0x08031DBA). The Play Room fast-forwards while it is set. mGBA keeps IWRAM directly after EWRAM, so in the emulator heap EWRAM = IWRAM base - 0x40000 (confirmed in the browser).

## Link play (2 players)

- `tools/link2.c` keeps the SD (all connected) bit of SIOCNT up to date every frame; with libmgba 0.10.2 the master never saw it and no transfers happened.
- `tools/link2.c` runs two GBAs in one process with a small multiplayer-mode (SIO_MULTI) link driver: the master's SIOCNT start latches both SIOMLT_SEND words, and after the transfer time each GBA gets SIOMULTI0-3, its ID and the SIO interrupt. Cores take turns by scanline. Build: `gcc -O2 -o tools/link2 tools/link2.c -lmgba`.
- Verified 2026-11-06: both GBAs pick Multiplayer, load a save, see the same "Choose your path" screen (the master chooses), and enter the same level with both heroes on screen (about 3.7 transfers per frame).
- Browser build (2026-11-06): libmgba 0.10.5 for wasm with emscripten 3.1.6 from apt (`emcmake cmake` with SDL/Qt/zlib/png/etc. off, then in CMakeCache.txt clear the HAVE_* checks emscripten fakes, keeping HAVE_STRDUP/STRNDUP/LOCALTIME_R/*LOCALE/STRTOF_L, and add `-DDISABLE_THREADING -D_GNU_SOURCE`). `tools/link/build.sh` links `tools/link/web.c` into link.js + link.wasm (~600 KB). Both GBAs run in about 4 ms a frame on a desktop, and runs are deterministic (same RAM hash every run).
- Play Room "Play together": each page runs both GBAs and exchanges only buttons through the room capability's presence (latest-wins, ~30 updates/s): `{f, k: last 40 frames of buttons, hs: RAM hash every 120 frames, pi/po: ping}`. Input delay = half the measured round trip + 3 frames (4-24). Host = player 1 (link master). Guest builds the game with the host's mod/stats/skills and must match its CRC; both saves travel in presence at the start. Tested with two simulated players at 40 ms and 150 ms one-way latency: 60 fps, matching hashes, both in the same level.
