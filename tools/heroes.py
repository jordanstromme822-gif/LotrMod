#!/usr/bin/env python3
"""Edit every hero's starting attributes.

  python3 tools/heroes.py rom.gba                         # show the table
  python3 tools/heroes.py rom.gba out.gba gimli strength 40 legolas accuracy 45 ...
  python3 tools/heroes.py rom.gba out.gba --all +10       # add 10 to every attribute of every hero

The original game sets starting attributes with numbers baked into its code (one block per
hero, function 0x08025D6C). The first edit replaces that function with a short routine that
reads from a table, so each hero and attribute can be changed on its own. The routine and
table live in the expanded part of the ROM, so the output is always 32 MB (see expand.py).
"""
import struct
import sys

from expand import expand

HEROES = ["frodo", "legolas", "aragorn", "gandalf", "eowyn", "gimli", "sam", "smeagol"]
# attribute -> offset in the player block (0x03003C00 + 0x1AC * player)
ATTRS = {"courage": 0x2A, "defense": 0x2C, "health": 0x2E, "accuracy": 0x30, "strength": 0x32}

FUNC = 0x25D6C          # original "set starting attributes" function (ROM offset)
JUMP_TABLE = 0x25D8C    # its 8-entry switch table, one case per hero
RESUME = 0x08025EB3     # where every original case ends up (Thumb address)
HOOK = 0x1000000        # our routine, ROM offset (CPU 0x09000000)
TABLE = 0x1000100       # hero table: 8 heroes x 16 bytes, u16 values in ATTRS order
MAGIC = b"LOTRMOD-HEROES\0\0"
MAGIC_AT = 0x10000E0


def original_stats(rom):
    """Read each hero's values out of the original code (movs/strh pairs)."""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    out = []
    for hid in range(8):
        case = struct.unpack_from("<I", rom, JUMP_TABLE + 4 * hid)[0] & ~1
        a = case - 0x08000000
        regs, stores = {}, {}
        for ins in md.disasm(bytes(rom[a:a + 0x40]), case):
            m, o = ins.mnemonic, ins.op_str
            if m == "movs" and "#" in o:
                r, v = o.split(", ")
                regs[r] = int(v[1:], 0)
            elif m == "strh" and "r0, #" in o:
                stores[int(o.split("#")[1].rstrip("]"), 0)] = regs[o.split(",")[0]]
            elif m == "b":
                stores[0x32] = regs["r1"]  # shared final store at 0x08025EB0
                break
        out.append({name: stores[off] for name, off in ATTRS.items()})
    return out


def hook_code():
    import keystone
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB)
    base = 0x09000000
    lit = base + 0x80
    lines = [
        "push {r4, lr}",
        "lsls r0, r0, #24", "lsrs r0, r0, #24",
        "lsls r4, r1, #24", "lsrs r4, r4, #24",
        "cmp r0, #7",
        "bhi done",
        "LDR r2, TABLE",
        "lsls r3, r0, #4", "adds r2, r2, r3",
        "LDR r1, PLAYERS",
        "movs r0, #0xd6", "lsls r0, r0, #1", "muls r0, r4, r0", "adds r0, r0, r1",
    ]
    for i, off in enumerate(ATTRS.values()):
        lines += [f"ldrh r1, [r2, #{2 * i}]", f"strh r1, [r0, #{off}]"]
    lines += ["done:", "LDR r3, RESUME", "bx r3"]
    # Resolve the three literal loads by hand (keystone has no literal pools for Thumb).
    literals = {"TABLE": TABLE + 0x08000000, "PLAYERS": 0x03003C00, "RESUME": RESUME}
    names = list(literals)
    code = b""
    addr = base
    asm = []
    for ln in lines:
        if ln.endswith(":"):
            asm.append(ln)
            continue
        if ln.startswith("LDR "):
            reg, name = ln[4:].split(", ")
            target = lit + 4 * names.index(name)
            ln = f"ldr {reg}, [pc, #{target - ((addr + 4) & ~3)}]"
        asm.append(ln)
        addr += 2
    enc, _ = ks.asm("\n".join(asm), base)
    code = bytes(enc)
    assert len(code) <= 0x80, len(code)
    pool = b"".join(struct.pack("<I", literals[n]) for n in names)
    return code.ljust(0x80, b"\0") + pool


def install(rom):
    rom = bytearray(expand(bytes(rom)))
    if rom[MAGIC_AT:MAGIC_AT + len(MAGIC)] == MAGIC:
        return rom
    stats = original_stats(rom)
    blob = hook_code()
    rom[HOOK:HOOK + len(blob)] = blob
    rom[MAGIC_AT:MAGIC_AT + len(MAGIC)] = MAGIC
    for hid, s in enumerate(stats):
        for i, name in enumerate(ATTRS):
            struct.pack_into("<H", rom, TABLE + 16 * hid + 2 * i, s[name])
    # Trampoline at the start of the old function: ldr r3,[pc,#0]; bx r3; .word hook|1
    rom[FUNC:FUNC + 8] = bytes([0x00, 0x4B, 0x18, 0x47]) + struct.pack("<I", 0x09000001)
    return rom


def read_table(rom):
    if len(rom) > MAGIC_AT and rom[MAGIC_AT:MAGIC_AT + len(MAGIC)] == MAGIC:
        return [{n: struct.unpack_from("<H", rom, TABLE + 16 * h + 2 * i)[0] for i, n in enumerate(ATTRS)} for h in range(8)]
    return original_stats(rom)


def set_stat(rom, hero, attr, value):
    h = HEROES.index(hero)
    i = list(ATTRS).index(attr)
    if not 0 <= value <= 999:
        raise SystemExit("Values must be 0-999")
    struct.pack_into("<H", rom, TABLE + 16 * h + 2 * i, value)


def show(rom):
    t = read_table(rom)
    print("hero      " + "".join(f"{a:>10}" for a in ATTRS))
    for h, row in zip(HEROES, t):
        print(f"{h:10}" + "".join(f"{row[a]:>10}" for a in ATTRS))


def main():
    a = sys.argv[1:]
    if len(a) < 1:
        raise SystemExit(__doc__)
    rom = bytearray(open(a[0], "rb").read())
    if rom[0xAC:0xB0] != b"BLRE":
        raise SystemExit("This doesn't look like the US/EU Return of the King ROM (game code BLRE).")
    if len(a) == 1:
        show(rom)
        return
    out, edits = a[1], a[2:]
    rom = install(rom)
    if edits[:1] == ["--all"]:
        delta = int(edits[1])
        for h in HEROES:
            for attr in ATTRS:
                cur = read_table(rom)[HEROES.index(h)][attr]
                set_stat(rom, h, attr, max(0, cur + delta))
        edits = edits[2:]
    if len(edits) % 3:
        raise SystemExit("Edits come in threes: hero attribute value")
    for i in range(0, len(edits), 3):
        hero, attr, value = edits[i].lower(), edits[i + 1].lower(), int(edits[i + 2])
        if hero not in HEROES or attr not in ATTRS:
            raise SystemExit(f"Heroes: {', '.join(HEROES)}. Attributes: {', '.join(ATTRS)}.")
        set_stat(rom, hero, attr, value)
    open(out, "wb").write(rom)
    show(rom)


if __name__ == "__main__":
    main()
