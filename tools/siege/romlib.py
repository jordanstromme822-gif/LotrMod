"""Read Return of the King level data straight from the ROM.

Runs the game's own decompressor (0x08019D54) and tile loader (0x080324C8) in
Unicorn, so no emulator dumps are needed. pip install unicorn.
"""
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_INTR, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

LEVELS = 0x08069A58      # 0x4C bytes per level
OBJECTS = 0x0806C0F0     # 12 bytes per level, +4 = object blob


def _lz77(data, n):
    out = bytearray(); i = 0
    while len(out) < n:
        f = data[i]; i += 1
        for b in range(8):
            if len(out) >= n: break
            if f & (0x80 >> b):
                x = data[i] << 8 | data[i + 1]; i += 2
                for _ in range((x >> 12) + 3): out.append(out[-((x & 0xFFF) + 1)])
            else:
                out.append(data[i]); i += 1
    return bytes(out)


class Rom:
    def __init__(self, path):
        self.rom = open(path, 'rb').read()[:0x1000000]
        mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        mu.mem_map(0x0, 0x4000)
        mu.mem_map(0x02000000, 0x40000)
        mu.mem_map(0x03000000, 0x8000)
        mu.mem_map(0x04000000, 0x1000)
        mu.mem_map(0x06000000, 0x20000)
        mu.mem_map(0x08000000, 0x1000000)
        mu.mem_write(0x08000000, self.rom)
        # IWRAM decompressor pointers used by type 4 / type 6 data: the game copies
        # these routines to IWRAM at boot. Copy them the same way (code_copy).
        self.mu = mu
        mu.hook_add(UC_HOOK_INTR, self._svc)
        mu.hook_add(UC_HOOK_MEM_WRITE, self._dma, begin=0x040000D4, end=0x040000DF)
        self._boot_iwram()

    def _boot_iwram(self):
        # The game copies its decompressors to IWRAM at boot (see recomp/game.toml
        # [[code_copy]]) and keeps pointers to them; set up the same here.
        for run, src, size in ((0x030035E0, 0x080002DC, 0x350), (0x03003940, 0x0800D1D4, 0x1F8)):
            self.mu.mem_write(run, self.rom[src - 0x08000000:src - 0x08000000 + size])
        for var, val in ((0x030035D0, 0x03003940), (0x03003930, 0x030035E0), (0x03005F8C, 0x02028000)):
            self.mu.mem_write(var, struct.pack('<I', val))

    def _svc(self, uc, intno, ud):
        pc = uc.reg_read(UC_ARM_REG_PC); op = uc.mem_read(pc - 2, 1)[0]
        if op in (0x11, 0x12):
            src = uc.reg_read(UC_ARM_REG_R0); dst = uc.reg_read(UC_ARM_REG_R1)
            n = struct.unpack('<I', uc.mem_read(src, 4))[0] >> 8
            uc.mem_write(dst, _lz77(bytes(uc.mem_read(src + 4, min(2 * n + 64, 0x09000000 - src - 4))), n))
            return
        if op == 0x0B:  # CpuSet
            src = uc.reg_read(UC_ARM_REG_R0); dst = uc.reg_read(UC_ARM_REG_R1); c = uc.reg_read(UC_ARM_REG_R2)
            n = c & 0x1FFFFF; w = 4 if c & 0x04000000 else 2
            if c & 0x01000000: uc.mem_write(dst, bytes(uc.mem_read(src, w)) * n)
            else: uc.mem_write(dst, bytes(uc.mem_read(src, n * w)))
            return
        raise RuntimeError('svc %#x at %#x' % (op, pc))

    def _dma(self, uc, access, addr, size, value, ud):
        if addr == 0x040000DC and size == 4 or (addr == 0x040000DE and size == 2):
            cnt = value if addr == 0x040000DC else value << 16
            if not cnt & 0x80000000: return
            src, dst = struct.unpack('<II', uc.mem_read(0x040000D4, 8))
            n = cnt & 0xFFFF or 0x4000; w = 4 if cnt & 0x04000000 else 2
            uc.mem_write(dst, bytes(uc.mem_read(src, n * w)))

    def call(self, fn, *args):
        mu = self.mu
        for r, v in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2), args): mu.reg_write(r, v)
        mu.reg_write(UC_ARM_REG_SP, 0x03007E00); mu.reg_write(UC_ARM_REG_LR, 0x0)
        mu.emu_start(fn | 1, 0x0, count=500000000)
        return mu.reg_read(UC_ARM_REG_R0)

    def decomp(self, src):
        dst = 0x02010000
        n = self.call(0x08019D54, src, dst)
        return bytes(self.mu.mem_read(dst, n))

    def u32(self, a): return struct.unpack('<I', self.rom[a - 0x08000000:a - 0x08000000 + 4])[0]
    def entry(self, L): return list(struct.unpack('<19I', self.rom[LEVELS - 0x08000000 + 0x4C * L:][:0x4C]))

    def tiles(self, tileset, idx_list):
        """Pixels (32 bytes, 4bpp) of tileset entries, loaded by the game's own routine."""
        lst = struct.pack('<H', len(idx_list)) + struct.pack('<%dH' % len(idx_list), *idx_list)
        self.mu.mem_write(0x02020000, lst)
        self.mu.mem_write(0x06000000, bytes(0x10000))
        self.mu.mem_write(0x02030000, struct.pack('<I', 0x00001F03))  # BGCNT word: charbase 0
        self.call(0x080324C8, tileset, 0x02020000, 0x02030000)
        v = bytes(self.mu.mem_read(0x06000000, 0x10000))
        return [v[32 * k:32 * k + 32] for k in range(len(idx_list))]
