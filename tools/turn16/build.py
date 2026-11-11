#!/usr/bin/env python3
"""Build the 16-facing hook (needs clang + ld.lld): turn16.bin (ROM 0x9F000) + turn16.sym."""
import os, subprocess
D = os.path.dirname(os.path.abspath(__file__))
def run(*a): subprocess.run(a, check=True, cwd=D)
run("python3", "tables.py")
run("clang", "--target=thumbv4t-none-eabi", "-mthumb", "-Os", "-ffreestanding", "-fno-builtin", "-fomit-frame-pointer",
    "-fno-pic", "-ffunction-sections", "-c", "turn16.c", "-o", "turn16.o")
run("ld.lld", "-T", "link.ld", "turn16.o", "-o", "turn16.elf")
run("llvm-objcopy", "-O", "binary", "turn16.elf", "turn16.bin")
syms = subprocess.run(["llvm-nm", "turn16.elf"], cwd=D, capture_output=True, text=True, check=True).stdout
with open(os.path.join(D, "turn16.sym"), "w") as f:
    for line in syms.splitlines():
        a, t, n = line.split()
        if t in "TtDdRr": f.write(f"{n} {a}\n")
print("size", os.path.getsize(os.path.join(D, "turn16.bin")))
