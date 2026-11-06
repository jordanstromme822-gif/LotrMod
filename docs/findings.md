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
  the 16 MB ROM is small (about 13 KB at `0xFFCB89`), so bigger text changes will mean
  growing the ROM to 32 MB, which GBA hardware and emulators support.

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
- `tools/ips.py`: make and apply IPS patches.
