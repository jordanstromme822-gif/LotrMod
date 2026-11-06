# Realm of Shadows

An original fantasy dungeon crawler that runs in the browser on phones and PCs.
The goal is Diablo II style online play: pick a saved character, enter a lobby,
and host or drop into anyone's game, up to 8 players.

## Play

- **Online:** once GitHub Pages is turned on, the game is at
  https://jordanstromme822-gif.github.io/LotrMod/
- **On your computer:** install [Node.js](https://nodejs.org) 20 or newer, then run `npm start`
  in this folder and open http://localhost:8080

Controls: WASD or arrows to move, mouse to aim, left click / 1 / Space to Slash,
2 Whirlwind, right click / 3 Firebolt, 4 Mend. On a phone, drag the left side of the
screen to move and tap the buttons; attacks aim at the nearest enemy.

## Roadmap

1. **Playable prototype** (done): one hero, four abilities, three enemy types, one dungeon.
2. **Online lobby and saves:** saved characters, a lobby, host or join games up to 8 players.
3. **Moddable content:** more heroes and abilities, random dungeon generator.
4. **Test with friends** on phones and PCs.

## Modding

Heroes, abilities, enemies and dungeons are plain data files in `client/data/`.
See [MODDING.md](MODDING.md).
