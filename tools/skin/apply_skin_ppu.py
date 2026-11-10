# Applies the skin tag edits to gba_ppu.cpp (works on the obj-ext/oam-ext tree too). Usage: apply_skin_ppu.py gba_ppu.cpp
import sys
p=sys.argv[1]; s=open(p).read()
assert 'g_skin_on' not in s
k=s.index('namespace gba {')
s=s[:k]+'''// Skin (HD texture pack, 2026-11-10): when on, the wide renderer also writes one tag per output
// pixel naming the 8x8 tile (VRAM slot, palette bank, texel, flips) that won the pixel, so the page
// can draw replacement art for known tiles. Off by default; costs nothing when off.
extern "C" int g_skin_on = 0;
extern "C" uint32_t* g_skin_ids = nullptr;
extern "C" uint32_t g_skin_w = 0, g_skin_h = 0;
'''+s[k:]
a='template<bool Ordered>\nvoid render_scanline_wide_impl('
assert s.count(a)==1
s=s.replace(a,'''static inline uint32_t skin_tag(uint32_t tile_addr, uint32_t bank, bool c256, uint32_t px,
                                uint32_t py, bool hf, bool vf, bool obj) {
    return 0x80000000u | ((tile_addr >> 5) & 0xFFFu) | ((bank & 15u) << 12) | (c256 ? 1u << 16 : 0u) |
        ((px & 7u) << 17) | ((py & 7u) << 20) | (hf ? 1u << 23 : 0u) | (vf ? 1u << 24 : 0u) | (obj ? 1u << 25 : 0u);
}
'''+a)
i=s.index(a); j=s.index('void render_scanline_wide(uint8_t* rgb')
w=s[i:j]
def wrep(a,b):
    global w
    c=w.count(a); assert c==1,(a[:70],c); w=w.replace(a,b)
wrep('''        bool target2 = false;
        bool valid = false;
    };''','''        bool target2 = false;
        bool valid = false;
        uint32_t sk = 0;
    };''')
wrep('''    auto submit = [&](uint32_t x, uint16_t color, int key, uint8_t layer,
                      bool target1, bool target2) {''','''    const bool skin = g_skin_on && g_skin_ids && out_w <= GbaPpu::kMaxRenderWidth;
    if (skin) g_skin_w = out_w;
    auto submit = [&](uint32_t x, uint16_t color, int key, uint8_t layer,
                      bool target1, bool target2, uint32_t sk = 0) {''')
wrep('''        cand.valid = true;
        if (key < top[x].key)''','''        cand.valid = true;
        cand.sk = sk;
        if (key < top[x].key)''')
wrep('''                            submit(output_x, load_u16_le(pal + index * 2u), candidate_key,
                                   static_cast<uint8_t>(layer), blend_enabled(output_x) && target1, target2);''',
'''                            submit(output_x, load_u16_le(pal + index * 2u), candidate_key,
                                   static_cast<uint8_t>(layer), blend_enabled(output_x) && target1, target2,
                                   skin ? skin_tag(char_base + (entry & 0x03FFu) * (color256 ? 64u : 32u),
                                                   entry >> 12, color256, px,
                                                   (entry & 0x0800u) ? 7u - (tex_y & 7u) : tex_y & 7u,
                                                   entry & 0x0400u, entry & 0x0800u, false) : 0u);''')
wrep('''                    submit(sx, load_u16_le(pal + index * 2u), key, static_cast<uint8_t>(layer),
                           blend_enabled(sx) && target1, target2);''',
'''                    submit(sx, load_u16_le(pal + index * 2u), key, static_cast<uint8_t>(layer),
                           blend_enabled(sx) && target1, target2,
                           skin ? skin_tag(char_base + (entry & 0x03ffu) * (color256 ? 64u : 32u),
                                           entry >> 12, color256, px, py,
                                           entry & 0x0400u, entry & 0x0800u, false) : 0u);''')
# generic text path: the submit right after "sample_blend" computation
g='''                   sample_blend && ((first_targets & (1u << layer)) != 0),
                   (second_targets & (1u << layer)) != 0);'''
wrep(g,'''                   sample_blend && ((first_targets & (1u << layer)) != 0),
                   (second_targets & (1u << layer)) != 0,
                   skin ? skin_tag(char_base + tile_num * (color256 ? 64u : 32u), palette_bank,
                                   color256, px, py, hflip, vflip, false) : 0u);''')
wrep('''            bool obj_target2 = (second_targets & (1u << 4)) != 0;
            auto emit_obj''','''            bool obj_target2 = (second_targets & (1u << 4)) != 0;
            bool obj_skin = false, obj_hf = false, obj_vf = false;
            auto emit_obj''')
wrep('''                submit(ux, color, key, 4, t1, obj_target2);''','''                submit(ux, color, key, 4, t1, obj_target2,
                       obj_skin ? skin_tag(tile_off, palette_bank, color256, px_in_tile, py_in_tile,
                                           obj_hf, obj_vf, true) : 0u);''')
wrep('''            bool hflip = (attr1 & 0x1000u) != 0;
            bool vflip = (attr1 & 0x2000u) != 0;''','''            bool hflip = (attr1 & 0x1000u) != 0;
            bool vflip = (attr1 & 0x2000u) != 0;
            obj_skin = skin; obj_hf = hflip; obj_vf = vflip;''')
wrep('''    GBA_RENDER_PHASE_MARK(profile, WideOutput);
    for (uint32_t x = 0; x < out_w; ++x) {''','''    GBA_RENDER_PHASE_MARK(profile, WideOutput);
    uint32_t* skin_row = nullptr;
    if (skin && y + static_cast<int>(oy) >= 0 && static_cast<uint32_t>(y + static_cast<int>(oy)) < g_skin_h)
        skin_row = g_skin_ids + static_cast<std::size_t>(y + static_cast<int>(oy)) * out_w;
    for (uint32_t x = 0; x < out_w; ++x) {''')
wrep('''            dst[0] = dst[1] = dst[2] = 0;
            if (hd) hd->black_column(x);
            continue;''','''            dst[0] = dst[1] = dst[2] = 0;
            if (hd) hd->black_column(x);
            if (skin_row) skin_row[x] = 0;
            continue;''')
wrep('''        if ((effect == 1 || top[x].layer == 4) &&
            top[x].target1 && second[x].valid && second[x].target2 &&
            !(top[x].layer == 4 && second[x].layer == 4)) {''','''        if (skin_row) {
            // Bit 26: alpha-blended with the layer below; bit 27: brightness fade.
            const bool ab = (effect == 1 || top[x].layer == 4) && top[x].target1 && second[x].valid &&
                second[x].target2 && !(top[x].layer == 4 && second[x].layer == 4);
            const bool fade = !ab && (effect == 2u || effect == 3u) && bldy != 0u && top[x].target1;
            skin_row[x] = top[x].sk ? (top[x].sk | (ab ? 1u << 26 : 0u) | (fade ? 1u << 27 : 0u)) : 0u;
        }
        if ((effect == 1 || top[x].layer == 4) &&
            top[x].target1 && second[x].valid && second[x].target2 &&
            !(top[x].layer == 4 && second[x].layer == 4)) {''')
s=s[:i]+w+s[j:]
open(p,'w').write(s); print('skin edits ok')
