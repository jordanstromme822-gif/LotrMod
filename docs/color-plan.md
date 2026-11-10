# Colour plan (redraw of heroes and map pieces)

Goal: redraw the game's own heroes and map pieces with a planned palette, using the
same rules a painting class would: value first, hue-shifted ramps, warm light against
cool shadow, and a clear focal hierarchy. Art stays the game's own pixels (recoloured and
repainted) or our own; nothing from other games.

## Rules

1. **Value first.** Every recolour keeps the game's own light-to-dark order, so shapes and
   animation read exactly as before. Colours are picked in OKLab/OKLCH so equal steps look equal.
2. **One light, one shadow.** Key light is warm (yellow, about 80 degrees in OKLCH), fill/shadow is
   cool blue-violet (about 285 degrees). Every ramp slides toward the warm hue in its lights and
   toward the shared violet in its shadows, so all materials meet in the same dark and stay in harmony.
3. **Chroma peaks in the mid tones** and falls off in the deepest shadow and top highlight.
4. **Focal hierarchy.** Environments use a narrower value band (OKLab L 0.15 to 0.84) and low
   chroma; heroes get the full band (0.13 to 0.94) and the strongest chroma, so they always pop.
5. **Neutral daylight base.** Per-level moods (Helm's Deep mist, Mordor red, night) stay in the
   Play Room's lighting pass (`LIGHT_LOOKS`) on top; fire is warm 25 to 40 degrees, added shadows
   lean blue-violet (agreed with the lighting thread). Foliage stays clearly green so the
   tree-sway pass still finds it.

## Ramps

`tools/colorplan/plan.py` defines one ramp per material (stone, stone-dark, moss, slate, earth,
grass, foliage, bark, water, snow, lava, ash; heroes: steel, ranger, skin, leather, wizard,
elf-green, dwarf-red, gold). A colour is mapped by its own lightness onto its material's ramp.

## Two layers

- **Palette pass** (native size): rewrite the game's 15-colour palettes with the ramps. Works on
  every animation frame and every screen that uses the palette at once.
- **4x repaint** (skin atlas, `tools/skin`): Scale2x twice on the palette indices, soften value
  inside each material, add form light from the top-left, selective outline, then snap every
  pixel to its ramp (8 steps per material). `tools/colorplan/paint4x.py`.

## Tools

```sh
gcc -O2 -o /tmp/run tools/run.c -lmgba
# capdir/dump.bin = VRAM 0x18000 + palette 0x400 + OAM 0x400 (+ IO), capdir/hd.state = save state
python3 tools/colorplan/scene.py rom.gba hd capdir           # before.png / after.png
python3 tools/colorplan/sample_hero.py capdir hero.png
python3 tools/colorplan/sample_tile.py capdir 150 40 64 64 tile.png
python3 tools/colorplan/board.py capdir hero.png tile.png board.png
```

First samples (Helm's Deep, Aragorn) are in the project files under `color-plan/`.

## Heroes (first pass)

`tools/colorplan/heroes.py` tags each of the six select-screen heroes' OBJ palette by material
and recolours it (capture: hero select ring, Right presses at frame 2300 of
`recomp/first-level.input`, then warp to Helm's Deep 46). Every hero shares the warm light and
one violet cast shadow / darkest colour.

| Hero | Dominant | Second | Accent |
| --- | --- | --- | --- |
| Aragorn | steel | ranger blue | leather |
| Gandalf | white robe (violet shadows) | silver hair | skin |
| Eowyn | wine dress | linen | blonde + Rohan green |
| Gimli | rust beard/tunic | steel | gold |
| Frodo | rust waistcoat | leather | Elven cloak |
| Legolas | elf green | Elven cloak | blonde + silver |

Sam and Smeagol are not on the select screen (`tools/unlockheroes.py`), still to do.
OBJ palette 2 (weapons and effects) is shared by many objects; the sample recolours it too.
