#!/usr/bin/env python3
"""Make or apply a BPS patch. Unlike IPS, BPS works on game files bigger than 16 MB.

  python3 tools/bps.py make original.gba modded.gba my-mod.bps
  python3 tools/bps.py apply original.gba my-mod.bps output.gba

Share only the .bps file. Each player applies it to their own copy of the game
(Floating IPS and the Rom Patcher JS web page both understand BPS).
"""
import sys
import zlib

SOURCE_READ, TARGET_READ = 0, 1


def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _read_num(buf, p):
    n, shift = 0, 1
    while True:
        x = buf[p]
        p += 1
        n += (x & 0x7F) * shift
        if x & 0x80:
            return n, p
        shift <<= 7
        n += shift


def make(src, dst):
    out = bytearray(b"BPS1") + _num(len(src)) + _num(len(dst)) + _num(0)
    i, n = 0, len(dst)
    target_rel = 0  # TargetCopy offsets are relative to where the previous one ended

    def run_len(at):  # length of a run of one repeated byte starting at `at`
        j = at
        while j < n and dst[j] == dst[at] and j - at < 1 << 24:
            j += 1
        return j - at

    while i < n:
        start = i
        if i < len(src) and src[i] == dst[i]:
            while i < n and i < len(src) and src[i] == dst[i]:
                i += 1
            out += _num(((i - start - 1) << 2) | SOURCE_READ)
        elif run_len(i) >= 16:
            # A long run of one byte (like the 0xFF fill of an expanded ROM): write the
            # byte once, then copy it forward from the output itself.
            length = run_len(i)
            out += _num(TARGET_READ) + dst[i:i + 1]
            off = i - target_rel
            out += _num(((length - 2) << 2) | 3) + _num((abs(off) << 1) | (off < 0))
            target_rel = i + length - 1
            i += length
        else:
            # Stay in TargetRead until 8 matching bytes or a long run follow, so short matches don't bloat the patch.
            while i < n:
                if i + 8 <= n and i < len(src) and src[i:i + 8] == dst[i:i + 8]:
                    break
                if run_len(i) >= 16:
                    break
                i += 1
            out += _num(((i - start - 1) << 2) | TARGET_READ) + dst[start:i]
    out += zlib.crc32(src).to_bytes(4, "little") + zlib.crc32(dst).to_bytes(4, "little")
    out += zlib.crc32(out).to_bytes(4, "little")
    return bytes(out)


def apply(src, patch):
    if patch[:4] != b"BPS1":
        raise SystemExit("not a BPS patch")
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise SystemExit("patch file is damaged")
    if zlib.crc32(src) != int.from_bytes(patch[-12:-8], "little"):
        raise SystemExit("this patch was made for a different version of the game file")
    p = 4
    src_size, p = _read_num(patch, p)
    dst_size, p = _read_num(patch, p)
    meta, p = _read_num(patch, p)
    p += meta
    dst = bytearray()
    src_rel = dst_rel = 0
    end = len(patch) - 12
    while p < end:
        data, p = _read_num(patch, p)
        action, length = data & 3, (data >> 2) + 1
        if action == 0:  # SourceRead
            dst += src[len(dst):len(dst) + length]
        elif action == 1:  # TargetRead
            dst += patch[p:p + length]
            p += length
        else:
            off, p = _read_num(patch, p)
            off = (-1 if off & 1 else 1) * (off >> 1)
            if action == 2:  # SourceCopy
                src_rel += off
                dst += src[src_rel:src_rel + length]
                src_rel += length
            else:  # TargetCopy
                dst_rel += off
                for _ in range(length):
                    dst.append(dst[dst_rel])
                    dst_rel += 1
    if len(dst) != dst_size or zlib.crc32(dst) != int.from_bytes(patch[-8:-4], "little"):
        raise SystemExit("patching failed: result doesn't match")
    return bytes(dst)


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] not in ("make", "apply"):
        raise SystemExit(__doc__)
    a = open(sys.argv[2], "rb").read()
    b = open(sys.argv[3], "rb").read()
    result = make(a, b) if sys.argv[1] == "make" else apply(a, b)
    open(sys.argv[4], "wb").write(result)
    print(f"wrote {sys.argv[4]} ({len(result)} bytes)")
