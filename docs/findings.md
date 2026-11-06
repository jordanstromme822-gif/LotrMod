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
