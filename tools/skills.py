#!/usr/bin/env python3
"""Show or change when each hero's five active skills unlock.

Each hero has a table of 6 skills x 6 bytes (the 6th skill is Herbal
Healing). Byte n of a skill row is the hero level needed before skill
level n+1 can be bought with skill points; 255 means never. The skill
screen reads these through 0x080422F0 (jump table at 0x08042340).

  python3 tools/skills.py rom.gba                              # show
  python3 tools/skills.py rom.gba out.gba aragorn 2 1 1 1 1 1  # skill 2 of Aragorn unlocks from level 1
  python3 tools/skills.py rom.gba out.gba --half               # halve every wait
"""
import sys

HEROES = ["frodo", "legolas", "aragorn", "gandalf", "eowyn", "gimli", "sam", "smeagol"]
TABLE = [0x28758E, 0x2875FA, 0x28761E, 0x287642, 0x287666, 0x28768A, 0x2875B2, 0x2875D6]
NAMES = [
    ["Knife Toss", "Snare", "Galadriel's Cloak", "The One Ring", "Ring's Persuasion"],
    ["White Knives", "Spread Fire", "Friend of Mirkwood", "Foraging", "Silent Stride"],
    ["Sweep", "King's Command", "Sword Throw", "Numenorean Will", "Call of the Dead"],
    ["Sword of Power", "Lightstrike", "Shield", "Blinding Aura", "Summon Gwaihir"],
    ["Double Strike", "Shieldmaiden of Rohan", "Rohan Sprint", "Shield Bash", "Forth Eorlingas!"],
    ["Axe Throw", "Whirling Attack", "Dwarven Rage", "Stoicism", "Earth Shatter"],
    ["Knife Toss", "Snare", "Galadriel's Cloak", "Cookpot Smash", "Samwise the Strong"],
    ["Berserk Attack", "Rock Throw", "Cower", "Gollum!", "Pitiful Wail"],
]


def show(rom):
    for h, name in enumerate(HEROES):
        print(name)
        for k in range(5):
            row = list(rom[TABLE[h] + 6 * k:TABLE[h] + 6 * k + 5])
            print(f"  {k + 1} {NAMES[h][k]:<22} {row}")


def main():
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    rom = bytearray(open(a[0], "rb").read())
    if len(a) == 1:
        return show(rom)
    out, rest = a[1], a[2:]
    if rest == ["--half"]:
        for h in range(8):
            for k in range(5):
                for l in range(5):
                    at = TABLE[h] + 6 * k + l
                    rom[at] = max(1, (rom[at] + 1) // 2)
    else:
        h, k, levels = HEROES.index(rest[0]), int(rest[1]) - 1, [int(x) for x in rest[2:7]]
        if not 0 <= k < 5 or len(levels) != 5 or not all(1 <= v <= 99 for v in levels):
            raise SystemExit("need: hero skill(1-5) five levels (1-99)")
        rom[TABLE[h] + 6 * k:TABLE[h] + 6 * k + 5] = bytes(levels)
    open(out, "wb").write(rom)
    show(rom)


if __name__ == "__main__":
    main()
