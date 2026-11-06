# LotrMod

Tools and notes for modding **The Lord of the Rings: The Return of the King** (Game Boy Advance,
USA/Europe, game code `BLRE`) and playing it together online.

The game itself is **not** in this repository and never should be. Mods are shared as patch
files (`.ips`) that each player applies to their own copy.

## What works so far

- Run the game headless in an emulator with scripted button presses, screenshots,
  RAM dumps, save states and write-watchpoints (`tools/run.c`).
- Dump all in-game text in all 5 languages (`tools/text.py`).
- Change a hero's starting attributes (`tools/stats.py`).
- Make and apply IPS patches (`tools/ips.py`).

See [docs/findings.md](docs/findings.md) for what we know about how the game is built.

## Setup (Linux, or WSL on Windows)

```sh
sudo apt-get install libmgba-dev python3 python3-pil
gcc -O2 -o tools/run tools/run.c -lmgba
```

## Examples

```sh
# Give Aragorn 50 Courage and make a patch you can share
python3 tools/stats.py rotk.gba modded.gba aragorn courage 50
python3 tools/ips.py make rotk.gba modded.gba aragorn-courage.ips

# Apply someone's patch to your own copy
python3 tools/ips.py apply rotk.gba aragorn-courage.ips rotk-modded.gba

# Dump the English text
python3 tools/text.py rotk.gba 0 > text-en.txt
```

Patches can also be applied with any IPS tool, such as Floating IPS on Windows or the
"Rom Patcher JS" web page, and the result plays in any GBA emulator (mGBA recommended).

## Plan

1. **Map the game file** (this step): text, hero stats, player 2, tooling.
2. **First mods:** stats, abilities, text and graphics as patch files.
3. **Bigger mods:** new characters and abilities by changing the game's code.
4. **Online multiplayer:** link-cable play over the internet with an emulator, and
   a look at whether 4 players is possible.
