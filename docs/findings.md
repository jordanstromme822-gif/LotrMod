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
- `tools/run`: in this libmgba build key bit 8 is L and bit 9 is R (the script names now match). Careful: the game sees the script's "R" as GBA L (0x200) and "L" as GBA R (0x100).
- Save slot pages (v122, tools/orcslots): PAGE at 0x0203F000; with page 2 every slot read/write goes to EWRAM 0x0203F010 (4 x 0x70) and its slot heads 0x0203F1D0, which the page keeps. R on the slot screen (0x080307F0, free since nodelete) or the page's Page button (FLIPREQ 0x0203F008) flips: read all headers, then redraw each slot's panel (0x08030DA0(slot, cursor)) and hero picture (0x080311E4(slot)). State 9 and 0x10 (pause menu) updates are wrapped (state table 0x0806C898, 0x0806C8EC) to take the page's flip and Undo requests.

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
- `tools/orcslots.py` (Jordan, 2026-11-08): 4 slots under the grid, one Orc Head (unique item 23, word 0xFFFF17FE) each, +1 Courage per head only from there. Count per player at EWRAM 0x0203FFE0 (saved in header 0x4B bits 5-7, cleared by the title screen); the backpack keepsake path returns "no bonus" for Orc Heads in slots 0-15 and our slots call it with slot 16; the text layer is shown from a copy (screenblock 0x1B) with rows 10-17 moved to 13-18 (one empty row dropped), except in Carve Rune. Text 418 (the Orc Head description) re-encoded at 0x9FE00. Code is C in tools/orcslots/, at 0x9F000. Slots are drawn dark red (grid box tiles shown with BG palette 6, a red copy of palette 2) with a faded Orc Head in empty ones (the same sprite in OBJ semi-transparent mode, blended 50/50 with BG0 by the screen's own BLDCNT 0x0148 / BLDALPHA 0x0808). OBJ palettes 8-15 belong to the 8 backpack item pictures (grid slot j uses palette j), so a separate faded palette is not possible there. Locked in 2-player games (A gives the "can't" sound); the saved count still applies there.
- Slots work like equipment slots (Jordan, 2026-11-08): an Orc Head's item menu Equip moves it into the next free slot ("All 4 Orc Head slots are full!" otherwise); A on a filled slot opens the equipment menu (Unequip, Discard; Discard asks "Are you sure?" unless Fast Discard is on); A on an empty slot gives the "can't" sound. Item menu: base 0x030041B0 (+8 Carve Rune row shown, +0xC choice = option id 0 Equip/Unequip, 1 Discard, 2 Carve Rune, 3 Move Item, 4 multiplayer; +0x10 substate; +0x14 Yes/No choice), option rows 0x03001FE8, option text 0x0802C5BC(option, choice) ("Unequip" when the cursor is 0-7), up/down in 0x0802C928 from 0x0802CCB4, A 0x0802C658, substate jump table 0x0802A81C (2 closes and redraws the description with 0x0802CFFC, 3 is "Are you sure?" whose Yes discards at 0x0802AA54, 8 shows a message until A or B). Hooks: bl at 0x0802A9D8 (menu A), 0x0802AA04 (description), 0x0802AA54 (discard); 0x0802CCC4 and 0x0802C5FC map cursors 20-23 to 0 so the menu moves and reads like an equipment slot's.

## Orc Head tiers (Jordan, 2026-11-08)

- Item text panel (v135, Jordan 2026-11-09): itemdesc_wrap and the Orc Head slot description copy each description to EWRAM 0x0203F520-0x0203F5FF (+0 count, +4 item, +8 name colour, +9 min level from 0x0802D2F8(item), +10 Backpack cursor from [0x03001FE0] + 0x62, +11 hero level too low, +12 name from 0x0802B064 with 0xDC as the game passes it (a width; a small number cuts the name to "..."), +0x38 text). The page shows it in Backpack state 10 when the cursor still matches, over the grid for worn gear (cursor 0-7) and over the worn gear otherwise.
- Item names: 0x0802B064(buf, item, maxlen) builds the name (callers 0x0802C4A2 backpack/shop description, 0x0802F2B4 ground label) and sets the label colour byte at 0x03003F70 + 0x7C * LOCAL_P + 0x78: 3 yellow (normal), 9 green (magic; 12 on the ground label in gameplay, state 1), 6 red (rare, set, unique). Unique items (category 14, index <= 25) take their name from the unique table and never use the prefix/suffix bytes, and the keepsake stat path ignores them too; the save keeps full item words. So an Orc Head's top 16 bits are free for its roll.
- Item description: 0x0802C47C(buf 0xC8, player, item, &x, &y, &tile) draws the name and "Min. Level" and returns the text drawn under it (0x0802CFFC draws it at y 0x68, width 0x76); callers 0x0802D206 (backpack), 0x0801E96E, 0x0801EB8A (shop).
- Stat names: TEXT(330 + stat). Stat routine 0x0802DDC4(slot, stat, player, signed byte delta). Ids: 17-21 attributes (Strength, Accuracy, Health, Defense, Courage), 22 Hit Points, 23 Spirit Points, 24 % Speed, 28 Spirit Points per hit, 29 Hit Points Regen, 30 Spirit Regen, 31 % Extra Gems, 32 % Extra Treasure, 40-42 Corruption/Fear/Poison resistance.
- Speed is already capped by the game: 0x08023804 uses min(100 + % Speed, 175). % Extra Treasure is read by enemy drops (0x0803A744) and chests (0x0802EF32); % Extra Gems by gem drops (0x0803AF52).
- Enemy drops: 0x0803A6E8(enemy): enemy + 0x61 type, + 0x65 killer; drop table 0x08057F78 (8 bytes per type, byte 0 is 45 for enemies that always drop, else 0; drop if rand(1,100) + it > 45); item roll 0x0803A77C(&item, player, find, type) (other callers 0x08014B9A, 0x0801E0BA, 0x0802EF3E, 0x080461B2) returns the ground kind (84 for an Orc Head); spawn 0x0802EFE8(x, y, kind, item, [sp] lifetime 0x708) with x/y from enemy + 0xAC/+ 0xB0. Random numbers: 0x0803A4BC(lo, hi) (kept in step between linked GBAs).
- Levels: [0x03004174] = level id L; its name is TEXT(0x88 + L) and its region 0x08037A74(L) (name TEXT(0x6B + R)). Black Gate is L 58 (region Ithilien), Cirith Ungol L 6-13, Pelennor Fields L 99-107 (Pelennor Beacon 90-92 and Pelennor Battle 93-98 are separate regions).
- Level select (v131, Jordan 2026-11-09): writing level L to 0x030041F8, 5 to 0x030041F4 and 0x81 to 0x030041F0 (pending state 1, uncommitted, as when a save loads) takes a 1-player game straight to L, from play or the pause menu. Mission start levels come from the multiplayer path tables at 0x08283030 (8 pointers to 5 entries of 4 bytes, level first): 51 32 88 2 25 / 109 32 125 93 99 / 51 113 128 97 69 / 79 117 6 27 18, then 82 (Moria), 121 (Amon Sul), 46 (Hornburg), 37 (Entwood). Region ranges are at 0x0806D20C (28 u16 pairs, read by 0x08037A74); with the text dump's numbering a level's name is TEXT(0x87 + L) and a region's TEXT(0x6A + R). In a 2-player game the same writes break the link ("Lost connection!"), so the page restarts both games from the saves and the link engine swaps the level in after the path screen (rotk_link_level).
- Saves: RAM save slot headers at 0x03005630 + 0x70 * slot; 0x0803CE24(src, slot) writes one to EEPROM (callers 0x08030F7C, 0x0803105E, 0x0803CC56), 0x0803CDE8(dst, slot) reads one (callers 0x0803CCDC, 0x0803CD14). Correction (v122): EEPROM blocks 0x32-0x3F are save slot 4 (slot k = blocks 8 + 14k, table 0x0806E104), not free space. The file header (blocks 0-7, RAM copy 0x030057F0: "ROTKGBA6", progress bits at +0x2C, checksum u16 at +0x3E so the 32 halfwords sum to 0) has bytes 8-0x2B unused (0xFF in the template 0x0806E0C4); 0x0803CD6C writes it when its checksum changed, 0x0803CE5C checks it at boot. Read all 4 slot headers: 0x0803CCBC (the save screen's init calls it every time it opens). Read/write blocks: 0x0803CF10 / 0x0803CF40(block, count, buf).
- Link messages: send 0x0803FDF0(type, w0, w1, w2) (case table 0x0803FE3C, index type - 1, copies up to 8 payload bytes into message + 4, then 0x0804006A queues it); receive dispatch 0x0803F610 (case table 0x0803F69C; r6 = message, r9 = sending player, r7 = 1 if from the other GBA; every GBA, the sender included, runs each message on the same frame). Types 1, 2, 4-9 and 0xB-0x12 are unused.
- Every gameplay frame: state 1 update 0x08031E44 calls 0x080391C4 at 0x08031ED0.
- `tools/orcslots.py` (v120): roll in the item word's top half (bits 15-14 tier, 13-12 difficulty table, 11-0 seed; tier 3 or table 3 = a head from before tiers). Slot heads per player at EWRAM 0x0203FF00, per save slot at 0x0203F280 (v122; saved XOR 0xC000 in the file header bytes 8 + 8k, all 0xFF = none). v120-v121 kept them in EEPROM blocks 0x32-0x34, the start of save slot 4, which broke slot 4 whenever another slot was saved, 2-player copies at 0x0203FF38, what is on each hero at 0x0203FE40. EWRAM 0x0203FE40-0x0203FF7F was checked unused (smooth60 uses 0x0203F600-0x0203FE3F).

## Frodo's crossbows (v125)

- Skill table entries are 40 bytes: +0 handler, +4 Spirit cost, +8 6 halfwords (value at level 0, then per level), +0x14 6 more. 0x08043764(player, skill, table, level) adds them up; skill k's level is hero data + 0x170 + k. Frodo is hero id 0 (Legolas 1); his table is 0x0806E94C. Snare's handler 0x080455C1 makes the trap object (attack id 0x5D, update 0x080456D9, touch 0x08016959, anim set 0x08287DD0, OBJ palette 3, owner + 0x9A trap count, checked at 0x0804367E against the second table). The trap's spot is the action point of Frodo's current frame (0x0800103C), which idle frames don't have.
- Damage without the hero's attack roll: 0x08010380(hero object, target, damage) adds hero data + 0x136, subtracts the target type's armor byte (0x08057518 + type * 20 + 0xC) and takes it off HP (+ 0x5A). Knife Toss (touch 0x080169B5, damage at + 0x88) and Snare use it.
- Arrows: 0x080337C8(owner, angle, 1) makes one (angle 0-31, 0 up, clockwise; 0x080329B4(dx, dy) gives it). For a hero it takes the worn quiver's arrow type from hero data + 0x44 (+ 0x93 on the arrow) and adds a trail (0x08026E88) from the arrow or the weapon's affixes. Positions: x at + 0xA4 / 0xAC / 0xCC, y at + 0xA8 / 0xB0 / 0xD0 (16.16). The arrow's own touch (0x08015425) is the hero's normal attack (0x0800F168).
- Objects: one list at 0x03002420 (next pointer at + 0). Awake foes have + 0xE8 & 0x801000 == 0x1000 and + 0xE8 & 0x10040400.
- Hero stats are halfwords at hero data + 0xA4 + 2 * stat (0 Melee, 1 Impaling, 2 Fire, 3 Poison Damage, 5 Damage, 47 Extra Projectiles, 50 Armor Piercing); an item's stats go on and off with 0x0802DB90(item, slot, player, remove).
- Anim sets: {tiles, frames, palette or 0, byte}. Frames: + 0xC u16 offsets (from + 0xC) per anim; each record is flags (0x20 LZ77, 0x40 the game's own packing, 0 raw) | part count, 0, width, height, u16 tile offset, u16 bytes, a 6-byte hitbox, then 4 bytes per OAM part. 0x08049B34 uploads a frame's tiles to VRAM. OBJ palette 3 is the same in every level.
- `tools/orcslots/crossbow.c`: Frodo's skill 1 handler calls Snare's for the object, then gives it our update and picture (8 directions, `xbgfx.c`). Crossbows per player at EWRAM 0x0203F360 (0x0203F360-0x0203F3FF).

## Frodo's skill rework (v126)

- Frodo's skills (table 0x0806E94C): 0 Knife Toss 0x080203BD (cost 25, damage 8 + 1 / level, now flat 8), 1 Snare (now Crossbow), 2 Galadriel's Cloak 0x08044D41 (cost 40; now Quick Drop), 3 One Ring 0x080204A5, 4 Ring's Persuasion 0x0802070D. Descriptions are texts 517-521; the skill's name is the text before " (Level".
- Knife Toss: the handler returns the knife (spawner 0x08043D74: + 0x8C angle, + 0xF8 facing = 0x0806F129[angle], velocity + 0xB4 / + 0xB8 = 0x0803288C(0x082821D0[angle * 8] / [+ 4], 0x48000), picture 0x08000D58(obj, 0x0806F2DC, 1, 0x08050418[facing]), facings above 4 flip with + 0xDF bit 0x10; + 0x8A / 0x8B hold the spawner's picture and auto-aim bytes). Update 0x08020471 (flight time + 0x50 via 0x08045584), touch 0x080169B5.
- The game's collision pass (IWRAM 0x03002F54-0x03003148) touches a knife against one foe only; a bounced knife never touched a second one, so `knife.c` homes it in and hits on its own (within 8 px).
- Stun: 0x08008A6C(obj, ticks) (+ 0x69 bit 0x80, state 0x12 / 0x1A then 5 / 0x1A for the time); King's Command style stars 0x0801C33C(hero, foe, ticks, 0xC, 8, 0, 8). + 0xE8 bit 0x4000 = can't be stunned.
- Ring's Persuasion charms with 0x080089AC(foe, ticks): + 0x69 |= 0x40 (cleared when it wears off), state 0x12 / 0x20, + 0xE8 |= 0x840204 (0x800000 = on Frodo's side).
- Can-cast check 0x08043484(player, skill), called at 0x08023896, 0x080293EE, 0x080431F6 (B), 0x080433E0 (quick skills: L + A / B / R use the skill numbers at hero data + 0x191 + n). Skills page buy: 0x080422F0(player, skill) = hero level needed (-1 = never), called by A at 0x08041FBA.
- Skill icons (Skills page, BG2, palette 4): per hero a pointer table (Frodo 0x0828773C, one per skill) to records of a 4-byte header + 12 raw 4bpp tiles (32 x 24, 4 x 3 tiles; the level pips under them are drawn separately). Frodo's Snare icon is at 0x785DB0, Galadriel's Cloak at 0x785F34; Sam has his own copies (0x7866C8, 0x78684C). `tools/orcslots/skillicons.py` (v127) draws crossbows into them.
- Sounds (v128, Jordan 2026-11-09: "traps should just make the bow shoot noise"): a crossbow plays Legolas's bow shot (sound 0x40, called at 0x08024892) once per volley and nothing else. Its bolts had played the arrow hit sounds through 0x08046FA0(sound, handle) with the handle kept in the bolt (+0x8E), and the break played sound 7; both are gone. The Snare handler's set-trap sound (0x6F) is muted by clearing the SFX bit (0x03005820 bit 2, which 0x08046EEC checks) around the call. Jordan reported all audio stopping (2026-11-09); the cause is not proven, these were the crossbow's only sound calls.
- Facing (v130, Jordan 2026-11-09: "the crossbow spins in a circle really fast"): the game's anim stepper 0x080022E4 (called for every object after its update) counts object + 0x20 down and then moves the frame at + 0x23 on, wrapping at the frames header's count (+ 6). Our 8 facings are 8 frames of one anim, so the crossbow cycled through them. At + 0x20 = 0 the stepper returns before it compares the shown frame (+ 0x22) with + 0x23 and uploads the new picture (0x080003A8), so the crossbow never turned (v131). v132: xb_new and xb_update set + 0x20 to 0xFF, so the stepper only counts down, shows the facing fire() picks with 0x08000DE8, and never moves on by itself.
- Skill entry + 0x21 bit 1 (Galadriel's Cloak only): the handler sets the hero's state itself; without it the cast state (0x35) calls the handler again every tick. Quick Drop clears it (0x6E9BD).
- Solo Wide engine: gp_hook (0x08031ED0) never ran there in tests, so Quick Drop's cooldown uses the game's tick counter 0x030041A4 (incremented by the gameplay update 0x08033000) instead.
- `tools/orcslots/knife.c` (knives in flight at EWRAM 0x0203F400-0x0203F4FF) and Quick Drop in `crossbow.c` (cooldown ticks per player at 0x0203F500, counted down by gp_hook).

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
- 0x89400-0x8946F: Frodo's Crossbow skill text (tools/orcslots.py, v125); the Orc Head code before it now runs to about 0x83E00.
- 0x9F000-0x9FFFF: free again (the Orc Head code moved to the French bank in v120). 0x7F000-0x844EB: Orc Head slots and tiers code (v126; Frodo's skill code included), picture and palettes (tools/orcslots.py); the French bank runs to 0x89863. The "Spanish" bank the tools use is really the Italian one (language table 0x289A10: En 0x7500C, Fr 0x7EE28, De 0x89864, Es 0x93C6C, It 0x9E330); French, German and Spanish are free as well.

## Arrows and quivers (Jordan, 2026-11-08)

- Arrows are category 7 items worn in the off-hand slot (hero + 0x44); the count is item byte 2 (the item roll at 0x0803AB34 gives 10-40), bits 4-7 are the rune like other items (all 15 values are real runes) and byte 3 is 0xFF (anything else reads as a set item). The name builder 0x0802B064 adds ": N arrows" for category 7. Text ids are one higher than the line numbers in `text-dumps` (TEXT(0x146) is "arrows").
- A shot calls 0x0802C410(player) (bl sites 0x080249A2, 0x08024A0C, 0x08024BEE, 0x08044AE0, each only when hero + 0x18C has flag 0x400, set by the stat routine when arrows are worn): count - 1; at 0 it clears flags 0x400 and 0x20 and deletes the quiver (0x0802C08C(2, player)); otherwise it shows the HUD count (0x03003F70 + 0x7C * player + 0x70 |= 0x4000, + 0x79 = 0x14). The HUD circle shows the worn count.
- Picking up arrows (0x0802AE68, called from pickup 0x0802ACE8) adds them to the worn quiver and then to matching backpack stacks, up to 99, if 0x0802EB08(a, b) says they match (category 7, same word apart from the count, count <= 98).
- The game logic runs 30 ticks a second (the gameplay frame 0x080391C4 runs every other refresh).
- Regenerating quivers (`tools/orcslots.py`, v121): 3% of rolled arrows (genitem_wrap). Off the hero they are written with byte 2 = 0x80 | max (full, since they refill in the pack too); worn, byte 2 is the live count and the max is EWRAM 0x0203FE80 + player. The save-slot packer (also used for the hero sent to the other GBA) writes the worn one in the pack form (header + 8 is the off-hand word), so a loaded or joined game starts with it full on both GBAs. There is no link message for it. In v121 the 2-player Wide engine also crashed when the Orc Head message's bonuses were put on inside the receive handler (an interpreted call into the hook code that ended at the SWI vector; the same code worked at its v120 addresses), so recv_c only stores the heads and the next gameplay frame (gp_hook) puts them on, on both GBAs. The gameplay frame refills 1 arrow every 30 ticks after the last shot and sets or clears flag 0x400; the 4 shot calls go to arrow_wrap (stops at 0, keeps the quiver); the 2 match checks go to same_wrap (never a regenerating quiver). Taking one off and on again keeps what it was missing, less what it refilled in play since.
- Arrow slots (`tools/orcslots.py`, v123, Jordan 2026-11-08): Legolas (hero id 1 at hero + 0x19F) gets 2 arrow-only slots under the Orc Head slots (cursor values 24, 25; arrow words at EWRAM 0x0203F2A0 + 8 * player, anything that isn't an arrow word reads as empty). Picking up (0x0802ACE8 calls 0x0802AE68 for arrows, bl at 0x0802AD0E -> apick_wrap): no worn quiver -> the game puts them on; a matching worn quiver -> the game merges (worn, then backpack stacks); otherwise a matching arrow slot (up to 99), then an empty arrow slot, then the game's backpack path. The page's L (ACYC 0x0203F313, read by gp_hook) rotates worn -> slots with the game's item stat routine 0x0802DB90(item, slot, player, remove) and weapon flags 0x0802D8E0(player); verified the hero's stats come back byte for byte after a full turn. Off in 2-player games. Drawn as OBJ: box tiles 940-955 (palette 2, a grid cell recoloured blue), arrow pictures 960-983 (palettes 4/5; the 10 arrow pictures were captured from the Backpack in mGBA without their frame lines), faded quiver 984-995 (palette 6, the Backpack's blue quiver icon blended with the box colour). OBJ palettes 0, 2, 4-6 are unused on the Backpack screen and the game reloads all OBJ palettes when it goes back to play; OBJ tiles above ~230 are free there. Legolas's item text moves to the bottom of the left side (rows 14-18) because the arrow row takes rows 13-15.
- 64 Kbit save chip (`tools/orcslots.py` BYTES, v124, Jordan 2026-11-08 "Yes bigger save file"): the game sets up the GBA EEPROM library once per access in 0x0803CF78, which calls the library's type setter 0x0804DC74 with 4 (4 Kbit, 64 blocks; table 0x08281FB8) or 0x40 (64 Kbit, 1024 blocks; table 0x08281FC4: size 0x2000, 14 address bits). Changing `movs r0, #4` at 0x0803CF8E to `#0x40` is enough: the game's own blocks (0-63) stay where they are, and an old 512-byte save reads as the first 64 blocks (mGBA grows the .sav to 8 KB, gbarecomp's EEPROM switches size on the first 17-bit request and keeps the bytes). Blocks 64-132 now hold what didn't fit: 64 marker "LOTRXT01" (stored reversed per block like all EEPROM data), 65-120 save page 2 (PBUF), 121-124 its slot heads (PHEAD), 125-132 the arrow slots per page and save slot (AKEEP, block 125 + 4 page + slot). XSTATE 0x0203F314: 1 = read from the save file, 2 = old save; the page then puts its stored copies in and sets XREQ 0x0203F315 to write them. The Wide engines need the constant changed in the generated C++ too (genpatch.py IMM).
- Arrow slots in 2-player games (v124): item pickups run in the item object update (0x0802F380 -> 0x0802ACE8) on every GBA for every player, so apick_wrap gives the same result on both GBAs once both have the same slots. Each GBA sends its player's 2 slot words once as link message 6 (send case 0x0803FE50 -> send4, receive case 0x0803F6B4 -> recv6); ALV 0x0203F340 + player = 1 once in. Quiver change: each GBA only has its own player's held keys (0x03004088 + 2 * player; the other player's stay 0), so the local GBA's gp_hook watches its player's GBA L and sends link message 7 (send 0x0803FE54 -> send4, receive 0x0803F6B8 -> recv7) when it flicks (changes twice within 8 ticks with no A, B or R in between); both GBAs change quivers when the message comes in. The page holds GBA L all the time in play for its Quick Skills, so a plain tap test doesn't work; the page's L button lets go of L (or presses it) for 110 ms instead, and the P2 bot presses L for 6 frames. The arrow slot menu (Unequip/Discard) stays locked in 2-player games (it would change only one GBA).
- Arrow slot saves: the EEPROM is full, so each save slot's 2 words go to AKEEP (0x0203F2D0, [page][slot][2], 64 bytes; AGEN 0x0203F310 counts writes, AREADY 0x0203F312 says the page put its stored copy in) through pack_c/unpack_c (ASAVED 0x0203F2B0, like SAVED) and save_wrap/load_wrap. The page keeps AKEEP in localStorage "rotk-arrows" and the account doc save-rotk-modded-arrows. Slot Undo puts the slot's arrows back too (UBUF + 0x78). Also fixed: hdr_slot only knew 3 save slots, so Orc Head slots of save slot 4 were never kept.

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
- Story map (v138, Jordan 2026-11-09): Story map button on the title screen / main menu. Data read from the game: mission starts (path table 0x08283030: King = Aragorn/Legolas/Gimli, Rohan = Eowyn, Wizard = Gandalf, Hobbits = Frodo/Sam, confirmed by the story-scene texts), and each level's exits. Exits are spawn records of type 3 (constructor 0x080325D8 via spawn table 0x08050444 index 2, touch 0x08014D41): in the level's spawn blob [0x03003234] (u16 group count, u16 group offsets, u16 item offsets) each record has +8 type, +0xC x, +0xE y, +0x12 entry point, +0x13 destination level. Script blob [0x03003248]: u16 count, u16 offsets, commands = u32 opcode + args, length table 0x08058210[op], handler table 0x08050838 (op n at index n-1); op 5 = dialogue (u16 id at +4), op 19 = level change (+4 level), op 28 = story scenes (+6 first slide, +4 level after). Side quests = levels whose scripts open the reward dialogue ids (Camps 30, Campsite 1, Corsair Camp 2, Waterfall 61, Edoras Fields 109, Deeping Outskirts 111). tools/storymap/ has the dump/parse scripts (mGBA runner warps to each level and dumps RAM) and the page code.
- Bonus maps tab (v139, Jordan 2026-11-09): Moria 82 Hall Top, 83 Long Stairs, 84 Treasure Hoards, 81 Hall, 49 Balin's Tomb; Amon Sul 121 Tower only (levels 118-120 have no map data); Hornburg 46 Fortress, 47 Valley (44, 45 empty); Entwood 37 Clearing, 38 Copse, 39 Entwash, 36 Campsite. Spawn record +0 holds the live object once spawned; enemy kind = object + 0x61, hit points = stats table 0x08057518 (20 bytes per kind) + 6 (orc 19, Uruk 72, trolls: kind 39 350, kind 40 250; Witch-king kind 69). Spawn type 29 = ordinary enemies (record +0x10 = species, kind from 0x08282838); type 22 spawns the trolls (Treasure Hoards 2 x kind 40, Balin's Tomb kind 39, Entwood Campsite kind 39 with 525 HP); type 24 = the Ringwraiths on Amon Sul. tools/storymap/kinds.py teleports the hero to each record and reads the kinds.
- Enemy counts (v140, Jordan 2026-11-09): stats table 0x08057518 (20 bytes per kind): +6 hit points, +8 experience (the kill handler 0x08011A28 passes it to 0x08010538, halved for some multiplayer kills). Enemy spawn records: r[16] picks a group of kinds (the game rolls one of them), so unspawned records are counted by the size class seen for the same (type, r[16]) elsewhere. Sizes: small < 40 HP, medium < 150, large >= 150; boss kinds 47 (Above), 60 (Shelob), 61 (Minas Tirith Gates, 100 HP / 600 XP), 63 (Steward's Tomb, 500 HP), 69 (Witch-king, 50 HP / 300 XP), 67 only in Black Chasm (999 HP / 5 XP; it also stands in the Docks and a Campsite). Kinds 83/84 (164 HP) are spawners. Kinds 74/75 (0 XP) in Orthanc are not enemies. tools/storymap/counts.py + model.py.
- Overhead map pictures (v142, Jordan 2026-11-09): tap/click a story map block to see the whole screen from above with no monsters. tools/storymap/cap.py warps to each level on a capture ROM where the exit touch literal (ROM 0x326A4) and the level-change script ops 19/28/44/56 point at a bx lr (0x0800C5F1), so teleports never leave the level; it turns off sprites (renderer disableOBJ), moves the hero by writing all six position fields (x at hero+0xA4/+0xAC/+0xCC, y at +0xA8/+0xB0/+0xD0, hero pointer [0x03003C00]) on a 160x100 grid, reads the camera at 0x030020F8/0x030020FC and pastes the top 136 rows of each shot (above the HUD). Shelob's Lair (115-117) draws its lantern glow on BG1, so BG1 is turned off there. Lossless WebP is about 3x smaller than lossy for these pixel maps (19 MB for 117 screens). The pictures are game graphics, so they live only in the private Play Room and project files, not in the repo; the phone page shows 'No picture' for now.
- Siege layout picker (v145, Jordan 2026-11-10): Siege tab on the story map with 8 spots (NW/NE corners, Black Gate, middle, SW/SE corners, Outer Gate approach, Helm's Deep fixed = level 46). Picks are saved to the account db doc data/users/<id>/siege-layout {slots:{nw,bg,ne,mid,sw,app,se,hd}} plus localStorage rotk-siege. Hero walking speed measured on Hornburg Valley: 1.5 pixels a frame (90 a second, camera moves the same), so hero positions are screen pixels. Walk time shown = long side of the screen picture / 90 (tools/storymap/walk.json). Exit records are mostly one per screen (entry points live elsewhere), so exit-to-exit distance wasn't usable.
- Siege v146 (Jordan 2026-11-10): 5 x 5 grid, keys r{row}c{col} (rows A-E top to bottom), Helm's Deep fixed at r5c3, defaults r1c3 Black Gate 58, r4c3 approach 47; old v145 keys (nw, bg, ne, mid, sw, app, se) are mapped over. Screens grouped by look (LOOK in storymap.js, sorted by eye from contact sheets): Woods, Plains, River & water, Ships & docks, Camps & houses, Snow & ice, Lava, Wasteland, Mountains, Red rock, Fortress, City, Dwarf halls, Caves, Ruins.
- Entrances and exits (v147, Jordan 2026-11-10): tools/storymap/ent.py warps to each level, puts the hero on every exit record (type 3, x/y at +0xC/+0xE, entry +0x12, destination +0x13) on the normal ROM and reads the level (0x03004174) and hero position (hero+0xAE x, +0xB2 y as whole pixels) after the move. 104 of 142 exits changed level; the rest are locked until a story step, lead to level 0 (bonus map end), or play a story scene into another level. Way-in points = arrival spots plus each level's warp start. Stored as thousandths of the picture in ee.json. Siege rotate/mirror is saved per spot as tf {r: 0/90/180/270, m: mirror, v: flip} in the siege-layout doc; plan only (the game's art is drawn from one angle, so in-game rotation isn't possible; left-right mirroring might be, later).

## Engine limits for big scenes (2026-11-10)

Measured on the original ROM in mGBA (Hornburg Valley, level 47) with `tools/engine/build_spawntest.py`
(test-only ROM that clones the level's enemy groups next to the hero) and `tools/runprof.c` (cycle-weighted profile).
- Objects: one pool of 256 objects of 0x148 bytes (0x0800064C: malloc 0x14800 at [0x030015B8], pool head 0x030015C0,
  alloc 0x0800169C -> 0x08030518) plus a 40-object pool at 0x030015C4. Live list 0x03002420. Monsters, missiles, items
  and effects all share it. 102 extra monsters (158 objects) still spawned and ran, so the pool is not the first limit.
- Groups: 0x0800C0EC(group) spawns every record of a spawn group whose +0 pointer is 0 (constructor table 0x08050440
  by record type +8); triggers call 0x0800C4AC(group, script). Hornburg Valley enemy records are types 25/26, trolls 22.
- Counters: 0x030041A4 counts game frames (30 a second), 0x0300411C counts VBlanks (60).
- Speed: game frames per second with extra monsters near the hero: +8: 30, +16: 30, +24: 25.5, +32: 21, +34 (all
  groups once): 16, +68: 11, +102: 8. With nothing extra the CPU idles about half of each frame in the VBlank wait
  (0x0802A3xx). The cost is spread over every object's update (AI, movement, animation, mixer), so a faster CPU is
  the main fix: about 2x for ~40 monsters on screen, 3x for ~70.
- Sprite tiles (OBJ VRAM, 1024 tiles): 0x08049AB8(gfx, bytes) finds a free run in the bitmap 0x030022D8 (1 bit per tile,
  ARM search copied to 0x03007690, returns 0xFFFF when full), marks it (0x08049C80) and uploads; free 0x08049C28.
  Frames are shared and refcounted per anim set (0x08003240..0x0800328E). With +68 monsters the search failed 403
  times in 60 frames (callers 0x080032A4 and 0x0800332A), so sprite frames go missing, and the search is ~13% of
  the CPU time. Big frames ask for up to 99 tiles.
- OAM: entries go through 0x08036540 into the shadow buffers at [0x03004B40] (two 0x400 halves), count byte
  0x03004220 (stops at 128), 0x080366A4 hides the rest. Seen at most 83 entries with +68 monsters, so 128 is close.
