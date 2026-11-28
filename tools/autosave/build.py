#!/usr/bin/env python3
"""Build the save-on-exit code (tools/autosave/autosave.c, at 0x08093000 in the free German text bank; needs clang +
ld.lld) into autosave.bin + autosave.sym. recomp/playroom/autosave-v278.py puts it into the Play Room page."""
import os, subprocess
D = os.path.dirname(os.path.abspath(__file__))
def run(*a): subprocess.run(a, check=True, cwd=D)
run("clang", "--target=thumbv4t-none-eabi", "-mthumb", "-Os", "-ffreestanding", "-fno-builtin", "-fomit-frame-pointer", "-fno-pic", "-c", "autosave.c", "-o", "autosave.o")
run("ld.lld", "-T", "link.ld", "-e", "0", "autosave.o", "-o", "autosave.elf")
run("llvm-objcopy", "-O", "binary", "autosave.elf", "autosave.bin")
syms = subprocess.run(["llvm-nm", "autosave.elf"], cwd=D, capture_output=True, text=True, check=True).stdout
with open(os.path.join(D, "autosave.sym"), "w") as f:
    for line in syms.splitlines():
        a, t, n = line.split()
        if t in "Tt": f.write(f"{n} {a}\n")
for f in ("autosave.o", "autosave.elf"): os.remove(os.path.join(D, f))
print("size", os.path.getsize(os.path.join(D, "autosave.bin")))
