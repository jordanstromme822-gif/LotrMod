// Turns a dungeon data file (rows of characters) into a map the game can use.
export const TILE = 32;

const SPAWN_CHARS = { g: 'ghoul', b: 'brute', a: 'archer' };

export function parseDungeon(data) {
  const rows = data.tiles;
  const h = rows.length;
  const w = Math.max(...rows.map((r) => r.length));
  const walls = [];
  const doors = new Set();
  const spawns = [];
  const potions = [];
  let start = null;
  let exit = null;

  for (let y = 0; y < h; y++) {
    walls.push([]);
    for (let x = 0; x < w; x++) {
      const ch = rows[y][x] ?? '#';
      walls[y].push(ch === '#');
      const cx = (x + 0.5) * TILE;
      const cy = (y + 0.5) * TILE;
      if (ch === 'S') start = { x: cx, y: cy };
      else if (ch === 'E') exit = { tx: x, ty: y, x: cx, y: cy };
      else if (ch === 'p') potions.push({ x: cx, y: cy });
      else if (ch === 'd') doors.add(y * w + x);
      else if (SPAWN_CHARS[ch]) spawns.push({ type: SPAWN_CHARS[ch], x: cx, y: cy });
    }
  }
  if (!start) throw new Error(`Dungeon "${data.name}" has no start tile (S)`);
  if (!exit) throw new Error(`Dungeon "${data.name}" has no exit tile (E)`);

  return {
    name: data.name,
    w,
    h,
    start,
    exit,
    spawns,
    potions,
    isDoor: (tx, ty) => doors.has(ty * w + tx),
    isWall(tx, ty) {
      if (tx < 0 || ty < 0 || tx >= w || ty >= h) return true;
      return walls[ty][tx];
    },
  };
}

// True when a circle at (x, y) with radius r overlaps any wall tile.
export function hitsWall(map, x, y, r) {
  const x0 = Math.floor((x - r) / TILE);
  const x1 = Math.floor((x + r) / TILE);
  const y0 = Math.floor((y - r) / TILE);
  const y1 = Math.floor((y + r) / TILE);
  for (let ty = y0; ty <= y1; ty++) {
    for (let tx = x0; tx <= x1; tx++) {
      if (!map.isWall(tx, ty)) continue;
      const nx = Math.max(tx * TILE, Math.min(x, (tx + 1) * TILE));
      const ny = Math.max(ty * TILE, Math.min(y, (ty + 1) * TILE));
      if ((x - nx) ** 2 + (y - ny) ** 2 < r * r) return true;
    }
  }
  return false;
}

// True when nothing solid blocks the straight line between two points.
export function lineOfSight(map, ax, ay, bx, by) {
  const dist = Math.hypot(bx - ax, by - ay);
  const steps = Math.ceil(dist / 8);
  for (let i = 1; i < steps; i++) {
    const t = i / steps;
    if (map.isWall(Math.floor((ax + (bx - ax) * t) / TILE), Math.floor((ay + (by - ay) * t) / TILE))) return false;
  }
  return true;
}
