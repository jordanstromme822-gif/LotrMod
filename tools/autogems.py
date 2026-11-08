#!/usr/bin/env python3
"""Pick up gems by walking over them (no R press).

How pickups work in the game:

  - Every item lying on the ground is an entity whose touch callback (entity + 0x18)
    is 0x0802F580. The collision loop in IWRAM calls it every frame the item and a
    hero overlap, with r0 = item, r1 = the hero.
  - The callback only picks the item up if that hero's player just pressed R
    (new presses at 0x03004080 + 2 * player, bit 0x100) and the item is the one the
    player is "looking at" (item + 0x8C + player, set by the item's update 0x0802F130
    when the hero is within 15 pixels; that's when its name shows in the HUD).
  - Item type is the byte at item + 0x60: 13 = "A Gem", 14 = "A Pile of @1 Gems"
    (text 568 + type). Gems are added to player + 0x184 (u16, capped at 0xFFFF).

The patch replaces those two checks (0x0802F59E-0x0802F5BF) with a call to a small
routine at 0x0809EC80 (in the unused Spanish text bank, so it needs the English-only
patch from tools/nocutscenes.py). For a gem it only checks that the toucher is that
player's own hero (the entity pointer at 0x03003C00 + 0x1AC * player), so allies and
enemies can't take it; every other item still needs R exactly as before. Both GBAs
run the same check in link play, so 2-player stays in step.

  python3 tools/autogems.py in.gba out.gba
"""
import sys

CODE_AT = 0x9EC80
CODE = bytes.fromhex(
    "10b54046603000780d3801280dd8032d0bd80d48d62252006a43801800680a1cf03a904201d1012010bd"
    "08486a008018008880225200104204d040468c304019007810bd002010bd003c000380400003")
SITE = 0x2F59E
OLD = bytes.fromhex("3749680040180188802040000840002800d1e5e140468c3040190078002800d1dee1")
NEW = bytes.fromhex("6ff06ffb00280cd1eae1c046c046c046c046c046c046c046c046c046c046c046c046")


def patch(rom: bytearray) -> bytearray:
    here = bytes(rom[SITE:SITE + len(OLD)])
    if here not in (OLD, NEW):
        raise SystemExit(f"unexpected bytes at {SITE:#x}; is this the BLRE ROM?")
    if rom[0x289A10 + 16:0x289A10 + 20] != bytes.fromhex("0c500708"):
        raise SystemExit("apply the English-only patch first (tools/nocutscenes.py); the code goes in the Spanish text bank")
    rom[SITE:SITE + len(NEW)] = NEW
    rom[CODE_AT:CODE_AT + len(CODE)] = CODE
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("gems are picked up by walking over them ->", sys.argv[2])
