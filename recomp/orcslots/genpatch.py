#!/usr/bin/env python3
"""Point the Wide engines' generated code at the Orc Head slots hooks (tools/orcslots.py).

  python3 genpatch.py <generated dir> <tools/orcslots/orcslots.sym>

The engines are native code made from the game, so a ROM patch that changes game code
is invisible to them. Like the noquickskill edits (README), the changed calls are made
in the generated C++ instead: a changed bl gets the hook as its constant target, and
two plain instructions that the ROM patch replaced with a bl become a call block (the
same shape the generator emits for a bl) plus an empty block. The hooks themselves are
not recompiled; they run in the runtime's interpreter and call back into native code.
Prints the shard files it changed; running it again after a hook build only moves the targets.
"""
import glob, os, re, sys

BL = [  # address of the bl's second half, hook symbol
    (0x08026016, "ac24_wrap"), (0x0803C2A8, "unpack_stub"), (0x08047F1A, "clear_stub"),
    (0x0802AC0C, "frame_hook"), (0x0802A706, "frame_hook"), (0x0802ABA0, "sound_wrap"),
    (0x0802A9DA, "menu_wrap"), (0x0802AA06, "desc_wrap"), (0x0802AA56, "discard_wrap"),
    # Orc Head tiers
    (0x08014B9C, "genitem_wrap"), (0x0801E0BC, "genitem_wrap"), (0x0802EF40, "genitem_wrap"),
    (0x0803A752, "genitem_wrap"), (0x080461B4, "genitem_wrap"),
    (0x0802C4A4, "name_wrap"), (0x0802F2B6, "name_wrap"),
    (0x0802D208, "itemdesc_wrap"), (0x0801E970, "itemdesc_wrap"), (0x0801EB8C, "itemdesc_wrap"),
    (0x08030F7E, "save_wrap"), (0x08031060, "save_wrap"), (0x0803CC58, "save_wrap"),
    (0x0803CCDE, "load_wrap"), (0x0803CD16, "load_wrap"), (0x08031ED2, "gp_hook"),
    # regenerating quivers
    (0x080249A4, "arrow_wrap"), (0x08024A0E, "arrow_wrap"), (0x08024BF0, "arrow_wrap"), (0x08044AE2, "arrow_wrap"),
    (0x0802AEAE, "same_wrap"), (0x0802AF24, "same_wrap"),
]
PAIRS = [(0x0802DBE0, "db90_stub"), (0x0803CC08, "pack_stub"), (0x0802CC60, "nav_stub"), (0x0802A854, "a_stub"),
         (0x0802CCC4, "mcur_stub"), (0x0802C5FC, "label_stub"),
         (0x0803A6EC, "drop_stub"), (0x0803A746, "find_cap"), (0x0802EF32, "chest_cap"), (0x0803AF54, "gem_cap"),
         (0x080307F0, "flip_r")]

CALL = """    /* {S:08X}  LotrMod Orc Head slots: bl {name} */
    {{
    g_cpu.R[15] = 0x{S:08X}u;
    if (runtime_should_yield()) return;
    if (g_runtime_insn_trace) runtime_insn_fp();
    uint32_t _cyc_{S:08X} = 3u + (uint32_t)g_runtime_waits.s16[8];
    uint32_t _blt_{S:08X} = 0x{T:08X}u;
    g_cpu.R[14] = 0x{R1:08X}u;
    g_cpu.R[15] = _blt_{S:08X};
    runtime_call_push_return(0x{R:08X}u);
    _cyc_{S:08X} += runtime_refill_cycles(_blt_{S:08X}, 1u);
    runtime_tick(_cyc_{S:08X});
    _cyc_{S:08X} = 0u;
    runtime_dispatch(_blt_{S:08X});
    if (g_cpu.R[15] != 0x{R:08X}u) {{ runtime_call_cancel_return(0x{R:08X}u); return; }}
    g_cpu.R[15] = 0x{R:08X}u;
    runtime_tick(_cyc_{S:08X});
    }}
"""
EMPTY = """    /* {S:08X}  LotrMod Orc Head slots: second half of the call above */
    {{
    g_cpu.R[15] = 0x{R:08X}u;
    }}
"""


def block(src, addr):
    """(start, end) of the instruction block for addr: from its comment line to its closing brace."""
    m = re.search(r"^    /\* %08X  .*\n" % addr, src, re.M)
    if not m:
        return None
    end = src.index("\n    }\n", m.end()) + len("\n    }\n")
    return m.start(), end


def main(gen, symfile):
    sym = {n: int(a, 16) for n, a in (l.split() for l in open(symfile))}
    changed = set()
    for path in sorted(glob.glob(os.path.join(gen, "recompiled_*.cpp"))):
        src = open(path).read()
        new = src
        for a, name in BL:
            pat = re.compile(r"(uint32_t _blt_%08X = )[^;]*;" % a)
            new = pat.sub(lambda m: m.group(1) + "0x%08Xu; /* LotrMod Orc Head slots: %s */" % (sym[name], name), new)
        for s, name in PAIRS:
            b = block(new, s)
            if not b:
                continue
            if "LotrMod Orc Head slots" in new[b[0]:b[1]]:   # patched before: just point it at the hook's current address
                new = re.sub(r"(uint32_t _blt_%08X = )0x[0-9A-F]+u;" % s, lambda m: m.group(1) + "0x%08Xu;" % sym[name], new)
                continue
            r = s + 4
            new = new[:b[0]] + CALL.format(S=s, T=sym[name], R=r, R1=r | 1, name=name) + new[b[1]:]
            b2 = block(new, s + 2)
            new = new[:b2[0]] + EMPTY.format(S=s + 2, R=r) + new[b2[1]:]
        if new != src:
            open(path, "w").write(new)
            changed.add(os.path.basename(path))
    print(" ".join(sorted(changed)))


if __name__ == "__main__":
    main(*sys.argv[1:3])
