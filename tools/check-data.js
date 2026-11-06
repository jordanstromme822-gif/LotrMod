// Checks the game data files for mistakes: `npm run check`
// Catches broken JSON, abilities or enemies that don't exist, and dungeons
// where the exit or a monster can't be reached from the start.
import { readFile, readdir } from 'node:fs/promises';

const dir = new URL('../client/data/', import.meta.url);
const problems = [];
const load = async (name) => {
  try {
    return JSON.parse(await readFile(new URL(name, dir), 'utf8'));
  } catch (err) {
    problems.push(`${name}: ${err.message}`);
    return null;
  }
};

const heroes = (await load('heroes.json')) ?? [];
const abilities = (await load('abilities.json')) ?? {};
const enemies = (await load('enemies.json')) ?? {};
const ABILITY_TYPES = ['melee', 'nova', 'projectile', 'heal'];
const SPAWNS = { g: 'ghoul', b: 'brute', a: 'archer' };
const TILES = new Set(['#', '.', 'd', 'S', 'E', 'p', ...Object.keys(SPAWNS)]);

for (const h of heroes) {
  for (const id of h.abilities ?? []) if (!abilities[id]) problems.push(`hero "${h.id}" uses unknown ability "${id}"`);
}
for (const [id, a] of Object.entries(abilities)) {
  if (!ABILITY_TYPES.includes(a.type)) problems.push(`ability "${id}" has unknown type "${a.type}" (use ${ABILITY_TYPES.join(', ')})`);
}
for (const v of Object.values(SPAWNS)) if (!enemies[v]) problems.push(`enemies.json is missing "${v}"`);

for (const file of await readdir(new URL('dungeons/', dir))) {
  const d = await load(`dungeons/${file}`);
  if (!d) continue;
  const rows = d.tiles;
  let start = null;
  const targets = [];
  rows.forEach((row, y) => [...row].forEach((ch, x) => {
    if (!TILES.has(ch)) problems.push(`${file}: unknown tile "${ch}" at row ${y + 1}, column ${x + 1}`);
    if (ch === 'S') start = [x, y];
    else if (ch !== '#' && ch !== '.' && ch !== 'd') targets.push([x, y, ch]);
  }));
  if (!start) { problems.push(`${file}: no start tile (S)`); continue; }
  if (!targets.some((t) => t[2] === 'E')) problems.push(`${file}: no exit tile (E)`);
  const seen = new Set([start.join()]);
  const queue = [start];
  while (queue.length) {
    const [x, y] = queue.shift();
    for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
      const ch = rows[ny]?.[nx] ?? '#';
      if (ch === '#' || seen.has(`${nx},${ny}`)) continue;
      seen.add(`${nx},${ny}`);
      queue.push([nx, ny]);
    }
  }
  for (const [x, y, ch] of targets) {
    if (!seen.has(`${x},${y}`)) problems.push(`${file}: "${ch}" at row ${y + 1}, column ${x + 1} can't be reached from the start`);
  }
}

if (problems.length) {
  console.error(`Found ${problems.length} problem(s):\n- ${problems.join('\n- ')}`);
  process.exit(1);
}
console.log('All game data looks good.');
