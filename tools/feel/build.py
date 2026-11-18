#!/usr/bin/env python3
"""Build the movement-feel routine (needs clang + ld.lld): feel.bin, placed by the Play Room page at ROM 0x8A000."""
import os, subprocess
D = os.path.dirname(os.path.abspath(__file__))
def run(*a): subprocess.run(a, check=True, cwd=D)
run("clang", "--target=thumbv4t-none-eabi", "-mthumb", "-Os", "-ffreestanding", "-fno-builtin", "-fomit-frame-pointer",
    "-fno-pic", "-ffunction-sections", "-c", "feel.c", "-o", "feel.o")
run("ld.lld", "-e", "hero_feel", "-Ttext=0x0808A000", "--section-start=.text.hero_feel=0x0808A000", "feel.o", "-o", "feel.elf")
run("llvm-objcopy", "-O", "binary", "-j", ".text.hero_feel", "-j", ".text", "feel.elf", "feel.bin")
print(subprocess.run(["llvm-nm", "feel.elf"], cwd=D, capture_output=True, text=True).stdout.strip())
print("size", os.path.getsize(os.path.join(D, "feel.bin")))
