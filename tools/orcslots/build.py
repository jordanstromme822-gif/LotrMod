#!/usr/bin/env python3
"""Build the Orc Head slots code (needs clang + ld.lld) and write orcslots.bin + orcslots.sym."""
import os, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
CF = ["clang"] + (["-DDEBUG_SPAWN"] if os.environ.get("DBG") else []) + ["--target=thumbv4t-none-eabi", "-mthumb", "-Os", "-ffreestanding", "-fno-builtin",
      "-fomit-frame-pointer", "-fno-pic", "-c"]
def run(*a): subprocess.run(a, check=True, cwd=D)
run(*CF, "orcslots.c", "-o", "orcslots.o")
run(*CF, "orcgfx.c", "-o", "orcgfx.o")
run(*CF, "arrowgfx.c", "-o", "arrowgfx.o")
run(*CF, "crossbow.c", "-o", "crossbow.o")
run(*CF, "xbgfx.c", "-o", "xbgfx.o")
run(*CF, "knife.c", "-o", "knife.o")
run("clang", "--target=thumbv4t-none-eabi", "-c", "stubs.s", "-o", "stubs.o")
run("ld.lld", "-T", "link.ld", "stubs.o", "orcslots.o", "orcgfx.o", "arrowgfx.o", "crossbow.o", "xbgfx.o", "knife.o", "-o", "orcslots.elf")
run("llvm-objcopy", "-O", "binary", "orcslots.elf", "orcslots.bin")
syms = subprocess.run(["llvm-nm", "orcslots.elf"], cwd=D, capture_output=True, text=True, check=True).stdout
with open(os.path.join(D, "orcslots.sym"), "w") as f:
    for line in syms.splitlines():
        a, t, n = line.split()
        if t in "TtDdRr": f.write(f"{n} {a}\n")
print("size", os.path.getsize(os.path.join(D, "orcslots.bin")))
