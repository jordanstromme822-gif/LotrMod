# Modding guide

Everything you can change lives in `client/data/`. Edit a file, save, and reload the page.
Run `npm run check` afterwards: it tells you in plain words if something is broken.

## Heroes (`heroes.json`)

Each hero is one entry in the list. Add another entry to add a new hero to the menu.

| Field | Meaning |
|---|---|
| `id` | Short unique name, no spaces |
| `name`, `description` | Shown on the hero menu |
| `color` | Body color, like `"#4a90d9"` |
| `maxHp`, `maxMana` | Starting health and mana |
| `manaRegen` | Mana gained per second |
| `speed` | Pixels per second (a tile is 32 pixels) |
| `abilities` | Up to 4 ability ids from `abilities.json`, in button order |

## Abilities (`abilities.json`)

Every ability has `name`, `type`, `cooldown` (seconds), `mana` (cost) and `color`.
The `type` decides what the other fields mean:

| Type | What it does | Fields |
|---|---|---|
| `melee` | Hits everything in a cone in front of you | `damage`, `range`, `arc` (degrees) |
| `nova` | Hits everything around you | `damage`, `radius` |
| `projectile` | Fires a bolt that hits the first enemy | `damage`, `speed`, `size`, `range` |
| `heal` | Restores your health | `amount` |

Damage grows 10% each level.

## Enemies (`enemies.json`)

`behavior` is `melee` (walks up and hits) or `ranged` (keeps distance and shoots).
Common fields: `hp`, `speed`, `damage`, `radius`, `attackCooldown`, `aggroRange` (how far away they notice you), `xp`.
Melee enemies use `attackRange`; ranged ones use `range`, `keepDistance` and `projectileSpeed`.

## Dungeons (`dungeons/*.json`)

A dungeon is a grid of characters, one string per row:

| Character | Meaning |
|---|---|
| `#` | Wall |
| `.` | Floor |
| `d` | Doorway |
| `S` | Where players start (exactly one) |
| `E` | Exit stairs (exactly one) |
| `p` | Healing potion |
| `g` / `b` / `a` | Ghoul / Brute / Bone Archer |

Random dungeons come later and will use these same pieces.
