#!/usr/bin/env python3
"""Make or apply an IPS patch.

  python3 tools/ips.py make original.gba modded.gba my-mod.ips
  python3 tools/ips.py apply original.gba my-mod.ips output.gba

Share only the .ips file. Each player applies it to their own copy of the game.
"""
import sys


def make(orig, mod):
    if len(mod) > 0x1000000:
        raise SystemExit("IPS patches only cover the first 16 MB of a ROM")
    out = bytearray(b"PATCH")
    i, n = 0, len(mod)
    while i < n:
        if i < len(orig) and orig[i] == mod[i]:
            i += 1
            continue
        start = i
        while i < n and (i >= len(orig) or orig[i] != mod[i]) and i - start < 0xFFFF:
            i += 1
        if start == 0x454F46:  # "EOF" offset would end the patch early
            start -= 1
        chunk = mod[start:i]
        out += start.to_bytes(3, "big") + len(chunk).to_bytes(2, "big") + chunk
    out += b"EOF"
    return bytes(out)


def apply(orig, patch):
    if patch[:5] != b"PATCH":
        raise SystemExit("not an IPS patch")
    data = bytearray(orig)
    p = 5
    while patch[p:p + 3] != b"EOF":
        off = int.from_bytes(patch[p:p + 3], "big")
        size = int.from_bytes(patch[p + 3:p + 5], "big")
        p += 5
        if size == 0:  # run-length record
            rle = int.from_bytes(patch[p:p + 2], "big")
            chunk = patch[p + 2:p + 3] * rle
            p += 3
        else:
            chunk = patch[p:p + size]
            p += size
        if off + len(chunk) > len(data):
            data.extend(b"\xff" * (off + len(chunk) - len(data)))
        data[off:off + len(chunk)] = chunk
    return bytes(data)


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] not in ("make", "apply"):
        raise SystemExit(__doc__)
    a = open(sys.argv[2], "rb").read()
    b = open(sys.argv[3], "rb").read()
    result = make(a, b) if sys.argv[1] == "make" else apply(a, b)
    open(sys.argv[4], "wb").write(result)
    print(f"wrote {sys.argv[4]} ({len(result)} bytes)")
