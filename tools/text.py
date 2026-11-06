#!/usr/bin/env python3
"""Dump the game's text.

  python3 tools/text.py rom.gba [language] > text.txt     # language 0-4: En, Fr, De, It, Es

Text is stored Huffman-compressed. A language bank is laid out as:
  u32 tree_size | Huffman tree (tree_size bytes, 4 bytes per node) |
  u32 offsets[] (relative to the bank start) | bit-packed strings
Bank pointers for the 5 languages are a u32 table at ROM 0x289A10.
Tree nodes are numbered from 0x100; each node is two u16 children (bit 0, bit 1).
A child <= 0xFF is a character, 0 ends the string. Bits are read low bit first.
The game's decoder is the function at 0x080299A0.
"""
import struct
import sys

LANG_TABLE = 0x289A10


def banks(rom):
    return [struct.unpack_from("<I", rom, LANG_TABLE + 4 * i)[0] - 0x08000000 for i in range(5)]


def decode(rom, bank, idx, maxlen=4000):
    tree_size = struct.unpack_from("<I", rom, bank)[0]
    tree = bank + 4
    table = tree + tree_size
    p = bank + struct.unpack_from("<I", rom, table + 4 * idx)[0]
    out = bytearray()
    node, bit, byte = 0x100, 0, rom[p]
    p += 1
    while len(out) < maxlen:
        while node > 0xFF:
            e = tree + (node - 0x100) * 4
            node = struct.unpack_from("<H", rom, e + 2 if (byte >> bit) & 1 else e)[0]
            bit += 1
            if bit == 8:
                bit, byte = 0, rom[p]
                p += 1
        if node == 0:
            break
        out.append(node)
        node = 0x100
    return bytes(out)


def count(rom, bank):
    tree_size = struct.unpack_from("<I", rom, bank)[0]
    table = bank + 4 + tree_size
    n = 0
    while True:  # entries run until the first offset that can't point at string data
        off = struct.unpack_from("<I", rom, table + 4 * n)[0]
        if off < 4 + tree_size + 4 * (n + 1) or bank + off >= len(rom) or off > 0x100000:
            break
        n += 1
    return n


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    lang = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    bank = banks(rom)[lang]
    for i in range(count(rom, bank)):
        text = decode(rom, bank, i).decode("latin-1").replace("\n", "\\n")
        print(f"{i}\t{text}")
