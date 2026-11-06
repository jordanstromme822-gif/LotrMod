import { TILE, parseDungeon, hitsWall, lineOfSight } from './dungeon.js';

const AUTO_AIM_RANGE = 450;

export class Game {
  constructor({ canvas, input, data, ui }) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.input = input;
    this.data = data;
    this.ui = ui;
    this.running = false;
    addEventListener('resize', () => this.resize());
    this.resize();
  }

  // ---------- setup ----------

  start(heroId) {
    const map = parseDungeon(this.data.dungeon);
    const def = this.data.heroes.find((h) => h.id === heroId);
    this.map = map;
    this.time = 0;
    this.camX = 0;
    this.camY = 0;
    this.state = 'playing';
    this.projectiles = [];
    this.effects = [];
    this.floaters = [];
    this.pickups = map.potions.map((p) => ({ ...p, kind: 'potion', amount: 35 }));
    this.enemies = map.spawns.map((s) => this.makeEnemy(s.type, s.x, s.y));
    this.abilities = def.abilities.map((id) => {
      const ab = this.data.abilities[id];
      if (!ab) throw new Error(`Hero "${def.id}" uses unknown ability "${id}"`);
      return { id, ...ab };
    });
    this.hero = {
      def,
      x: map.start.x,
      y: map.start.y,
      r: def.radius ?? 12,
      hp: def.maxHp,
      maxHp: def.maxHp,
      mana: def.maxMana,
      maxMana: def.maxMana,
      facing: { x: 1, y: 0 },
      cooldowns: this.abilities.map(() => 0),
      level: 1,
      xp: 0,
      xpNext: 50,
      power: 1,
      hurt: 0,
    };
    this.ui.setAbilities(this.abilities);
    if (!this.running) {
      this.running = true;
      this.last = performance.now();
      requestAnimationFrame((t) => this.frame(t));
    }
  }

  makeEnemy(type, x, y) {
    const def = this.data.enemies[type];
    if (!def) throw new Error(`Dungeon uses unknown enemy "${type}"`);
    return { def, x, y, r: def.radius, hp: def.hp, maxHp: def.hp, cd: Math.random(), aggro: false, hurt: 0, dead: false };
  }

  resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.dpr = dpr;
    this.vw = innerWidth;
    this.vh = innerHeight;
    this.canvas.width = Math.round(this.vw * dpr);
    this.canvas.height = Math.round(this.vh * dpr);
    // Show roughly 12 tiles across the short side of the screen.
    this.zoom = Math.max(0.75, Math.min(1.6, Math.min(this.vw, this.vh) / (TILE * 12)));
  }

  frame(t) {
    const dt = Math.min((t - this.last) / 1000, 0.05);
    this.last = t;
    if (this.state === 'playing') this.update(dt);
    else this.updateEffects(dt);
    this.render();
    requestAnimationFrame((n) => this.frame(n));
  }

  // ---------- simulation ----------

  update(dt) {
    this.time += dt;
    const hero = this.hero;

    // Movement
    const mv = this.input.move();
    if (mv.x || mv.y) {
      this.moveBody(hero, mv.x * hero.def.speed * dt, mv.y * hero.def.speed * dt);
      const len = Math.hypot(mv.x, mv.y);
      hero.facing = { x: mv.x / len, y: mv.y / len };
    }

    // Regen and cooldowns
    hero.mana = Math.min(hero.maxMana, hero.mana + hero.def.manaRegen * dt);
    hero.cooldowns = hero.cooldowns.map((c) => Math.max(0, c - dt));
    hero.hurt = Math.max(0, hero.hurt - dt);

    // Abilities
    const aim = this.aimDirection();
    this.abilities.forEach((ab, i) => {
      if (!this.input.slotHeld(i) || hero.cooldowns[i] > 0) return;
      if (hero.mana < ab.mana) {
        if (!this.noManaAt || this.time - this.noManaAt > 1) {
          this.noManaAt = this.time;
          this.floater(hero.x, hero.y - 24, 'Not enough mana', '#7aa7ff');
        }
        return;
      }
      hero.mana -= ab.mana;
      hero.cooldowns[i] = ab.cooldown;
      if (aim) hero.facing = aim;
      this.useAbility(ab, aim ?? hero.facing);
    });

    this.updateEnemies(dt);
    this.updateProjectiles(dt);
    this.updateEffects(dt);

    // Pickups
    this.pickups = this.pickups.filter((p) => {
      if (Math.hypot(p.x - hero.x, p.y - hero.y) > hero.r + 10) return true;
      if (hero.hp >= hero.maxHp) return true;
      const healed = Math.min(p.amount, hero.maxHp - hero.hp);
      hero.hp += healed;
      this.floater(hero.x, hero.y - 20, `+${Math.round(healed)}`, '#6ee07a');
      return false;
    });

    // Exit
    const tx = Math.floor(hero.x / TILE);
    const ty = Math.floor(hero.y / TILE);
    if (tx === this.map.exit.tx && ty === this.map.exit.ty) {
      this.state = 'won';
      const slain = this.enemies.filter((e) => e.dead).length;
      this.ui.showOverlay('Dungeon cleared', `You escaped ${this.map.name} at level ${hero.level}, defeating ${slain} of ${this.enemies.length} foes.`);
    }
  }

  aimDirection() {
    const hero = this.hero;
    if (!this.input.touchMode && this.input.mouse.active) {
      const wx = this.input.mouse.x / this.zoom + this.camX;
      const wy = this.input.mouse.y / this.zoom + this.camY;
      const dx = wx - hero.x;
      const dy = wy - hero.y;
      const len = Math.hypot(dx, dy);
      return len > 1 ? { x: dx / len, y: dy / len } : null;
    }
    // Touch: aim at the nearest visible enemy.
    let best = null;
    let bestD = AUTO_AIM_RANGE;
    for (const e of this.enemies) {
      if (e.dead) continue;
      const d = Math.hypot(e.x - hero.x, e.y - hero.y);
      if (d < bestD && lineOfSight(this.map, hero.x, hero.y, e.x, e.y)) {
        best = e;
        bestD = d;
      }
    }
    if (!best) return null;
    return { x: (best.x - hero.x) / bestD, y: (best.y - hero.y) / bestD };
  }

  useAbility(ab, dir) {
    const hero = this.hero;
    const dmg = (base) => Math.round(base * hero.power);
    switch (ab.type) {
      case 'melee': {
        const half = (ab.arc * Math.PI) / 360;
        const facing = Math.atan2(dir.y, dir.x);
        for (const e of this.enemies) {
          if (e.dead) continue;
          const dx = e.x - hero.x;
          const dy = e.y - hero.y;
          if (Math.hypot(dx, dy) > ab.range + e.r + hero.r) continue;
          let diff = Math.abs(Math.atan2(dy, dx) - facing);
          if (diff > Math.PI) diff = 2 * Math.PI - diff;
          if (diff <= half) this.damageEnemy(e, dmg(ab.damage));
        }
        this.effects.push({ type: 'arc', x: hero.x, y: hero.y, angle: facing, half, range: ab.range + hero.r, color: ab.color, t: 0, life: 0.18 });
        break;
      }
      case 'nova': {
        for (const e of this.enemies) {
          if (!e.dead && Math.hypot(e.x - hero.x, e.y - hero.y) <= ab.radius + e.r) this.damageEnemy(e, dmg(ab.damage));
        }
        this.effects.push({ type: 'ring', x: hero.x, y: hero.y, radius: ab.radius, color: ab.color, t: 0, life: 0.35 });
        break;
      }
      case 'projectile': {
        this.projectiles.push({
          x: hero.x + dir.x * hero.r,
          y: hero.y + dir.y * hero.r,
          vx: dir.x * ab.speed,
          vy: dir.y * ab.speed,
          r: ab.size,
          damage: dmg(ab.damage),
          life: ab.range / ab.speed,
          team: 'hero',
          color: ab.color,
        });
        break;
      }
      case 'heal': {
        const healed = Math.min(ab.amount, hero.maxHp - hero.hp);
        hero.hp += healed;
        this.floater(hero.x, hero.y - 20, `+${Math.round(healed)}`, ab.color);
        this.effects.push({ type: 'ring', x: hero.x, y: hero.y, radius: 30, color: ab.color, t: 0, life: 0.5 });
        break;
      }
      default:
        console.warn(`Unknown ability type "${ab.type}"`);
    }
  }

  updateEnemies(dt) {
    const hero = this.hero;
    for (const e of this.enemies) {
      if (e.dead) continue;
      const d = e.def;
      e.cd -= dt;
      e.hurt = Math.max(0, e.hurt - dt);
      const dx = hero.x - e.x;
      const dy = hero.y - e.y;
      const dist = Math.hypot(dx, dy) || 1;
      const sees = dist < d.aggroRange * 1.5 && lineOfSight(this.map, e.x, e.y, hero.x, hero.y);
      if (!e.aggro && dist < d.aggroRange && sees) e.aggro = true;
      if (!e.aggro) continue;
      const ux = dx / dist;
      const uy = dy / dist;
      const step = d.speed * dt;

      if (d.behavior === 'ranged') {
        if (dist > d.range || !sees) this.moveBody(e, ux * step, uy * step);
        else if (dist < d.keepDistance) this.moveBody(e, -ux * step, -uy * step);
        if (sees && dist <= d.range && e.cd <= 0) {
          e.cd = d.attackCooldown;
          this.projectiles.push({ x: e.x, y: e.y, vx: ux * d.projectileSpeed, vy: uy * d.projectileSpeed, r: 4, damage: d.damage, life: (d.range * 1.3) / d.projectileSpeed, team: 'enemy', color: '#e6e0c8' });
        }
      } else {
        const reach = d.attackRange + e.r + hero.r;
        if (dist > reach) this.moveBody(e, ux * step, uy * step);
        else if (e.cd <= 0) {
          e.cd = d.attackCooldown;
          this.damageHero(d.damage);
        }
      }
    }

    // Keep enemies from stacking on top of each other.
    const live = this.enemies.filter((e) => !e.dead);
    for (let i = 0; i < live.length; i++) {
      for (let j = i + 1; j < live.length; j++) {
        const a = live[i];
        const b = live[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const overlap = a.r + b.r - dist;
        if (overlap > 0) {
          const px = (dx / dist) * overlap * 0.5;
          const py = (dy / dist) * overlap * 0.5;
          this.moveBody(a, -px, -py);
          this.moveBody(b, px, py);
        }
      }
    }
  }

  updateProjectiles(dt) {
    const hero = this.hero;
    this.projectiles = this.projectiles.filter((p) => {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life -= dt;
      if (p.life <= 0 || hitsWall(this.map, p.x, p.y, p.r)) {
        this.effects.push({ type: 'spark', x: p.x, y: p.y, color: p.color, t: 0, life: 0.2 });
        return false;
      }
      if (p.team === 'hero') {
        for (const e of this.enemies) {
          if (!e.dead && Math.hypot(e.x - p.x, e.y - p.y) < e.r + p.r) {
            this.damageEnemy(e, p.damage);
            this.effects.push({ type: 'spark', x: p.x, y: p.y, color: p.color, t: 0, life: 0.25 });
            return false;
          }
        }
      } else if (this.state === 'playing' && Math.hypot(hero.x - p.x, hero.y - p.y) < hero.r + p.r) {
        this.damageHero(p.damage);
        return false;
      }
      return true;
    });
  }

  updateEffects(dt) {
    this.effects = this.effects.filter((fx) => (fx.t += dt) < fx.life);
    this.floaters = this.floaters.filter((f) => {
      f.t += dt;
      f.y -= 30 * dt;
      return f.t < 0.9;
    });
  }

  moveBody(b, dx, dy) {
    // Small steps so fast movers slide along walls instead of stopping short.
    const steps = Math.max(1, Math.ceil(Math.max(Math.abs(dx), Math.abs(dy)) / 4));
    const sx = dx / steps;
    const sy = dy / steps;
    for (let i = 0; i < steps; i++) {
      if (sx && !hitsWall(this.map, b.x + sx, b.y, b.r)) b.x += sx;
      if (sy && !hitsWall(this.map, b.x, b.y + sy, b.r)) b.y += sy;
    }
  }

  damageEnemy(e, amount) {
    e.hp -= amount;
    e.hurt = 0.12;
    e.aggro = true;
    this.floater(e.x, e.y - e.r - 6, String(amount), '#fff2c0');
    if (e.hp > 0) return;
    e.dead = true;
    this.gainXp(e.def.xp);
    if (Math.random() < 0.15) this.pickups.push({ kind: 'potion', x: e.x, y: e.y, amount: 25 });
  }

  damageHero(amount) {
    const hero = this.hero;
    if (this.state !== 'playing') return;
    hero.hp -= amount;
    hero.hurt = 0.2;
    this.floater(hero.x, hero.y - 22, `-${amount}`, '#ff6b5e');
    if (hero.hp <= 0) {
      hero.hp = 0;
      this.state = 'dead';
      this.ui.showOverlay('You have fallen', `You reached level ${hero.level} in ${this.map.name}.`);
    }
  }

  gainXp(xp) {
    const hero = this.hero;
    hero.xp += xp;
    while (hero.xp >= hero.xpNext) {
      hero.xp -= hero.xpNext;
      hero.xpNext = Math.round(hero.xpNext * 1.5);
      hero.level += 1;
      hero.maxHp += 12;
      hero.maxMana += 6;
      hero.hp = hero.maxHp;
      hero.mana = hero.maxMana;
      hero.power += 0.1;
      this.floater(hero.x, hero.y - 34, `Level ${hero.level}!`, '#d9b45a');
      this.effects.push({ type: 'ring', x: hero.x, y: hero.y, radius: 50, color: '#d9b45a', t: 0, life: 0.6 });
    }
  }

  floater(x, y, text, color) {
    this.floaters.push({ x, y, text, color, t: 0 });
  }

  // ---------- drawing ----------

  render() {
    const { ctx, hero, map, zoom, dpr } = this;
    const viewW = this.vw / zoom;
    const viewH = this.vh / zoom;
    this.camX = hero.x - viewW / 2;
    this.camY = hero.y - viewH / 2;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#0d0b10';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    const s = dpr * zoom;
    ctx.setTransform(s, 0, 0, s, -this.camX * s, -this.camY * s);

    // Tiles
    const x0 = Math.max(0, Math.floor(this.camX / TILE));
    const y0 = Math.max(0, Math.floor(this.camY / TILE));
    const x1 = Math.min(map.w - 1, Math.floor((this.camX + viewW) / TILE));
    const y1 = Math.min(map.h - 1, Math.floor((this.camY + viewH) / TILE));
    const floorShades = ['#2a2430', '#2d2633', '#28222d', '#2f2835'];
    for (let ty = y0; ty <= y1; ty++) {
      for (let tx = x0; tx <= x1; tx++) {
        const px = tx * TILE;
        const py = ty * TILE;
        if (map.isWall(tx, ty)) {
          if (map.isWall(tx, ty + 1)) {
            ctx.fillStyle = '#141017';
            ctx.fillRect(px, py, TILE, TILE);
          } else {
            // Wall face visible from below
            ctx.fillStyle = '#4a3f52';
            ctx.fillRect(px, py, TILE, TILE);
            ctx.fillStyle = '#5b4e63';
            ctx.fillRect(px, py, TILE, 6);
            ctx.fillStyle = '#3a3141';
            ctx.fillRect(px + (ty % 2 ? 0 : TILE / 2), py + 14, 2, TILE - 14);
          }
        } else {
          ctx.fillStyle = floorShades[((tx * 7) ^ (ty * 13)) & 3];
          ctx.fillRect(px, py, TILE, TILE);
          if (map.isDoor(tx, ty)) {
            ctx.fillStyle = '#5a4128';
            ctx.fillRect(px + 2, py + 2, TILE - 4, TILE - 4);
          }
        }
      }
    }

    // Exit stairs
    const ex = map.exit.tx * TILE;
    const ey = map.exit.ty * TILE;
    for (let i = 0; i < 4; i++) {
      ctx.fillStyle = `rgb(${120 - i * 25}, ${100 - i * 22}, ${60 - i * 12})`;
      ctx.fillRect(ex + 3, ey + 3 + i * 7, TILE - 6, 6);
    }
    ctx.strokeStyle = `rgba(217, 180, 90, ${0.5 + 0.3 * Math.sin(this.time * 3)})`;
    ctx.lineWidth = 2;
    ctx.strokeRect(ex + 1, ey + 1, TILE - 2, TILE - 2);

    // Pickups
    for (const p of this.pickups) {
      const bob = Math.sin(this.time * 4 + p.x) * 2;
      ctx.fillStyle = '#c23b32';
      ctx.beginPath();
      ctx.arc(p.x, p.y + bob, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#e8d9b0';
      ctx.fillRect(p.x - 2, p.y - 10 + bob, 4, 4);
    }

    // Enemies
    for (const e of this.enemies) {
      if (e.dead) {
        ctx.fillStyle = 'rgba(60, 20, 20, 0.5)';
        ctx.beginPath();
        ctx.ellipse(e.x, e.y + 4, e.r, e.r * 0.5, 0, 0, Math.PI * 2);
        ctx.fill();
        continue;
      }
      this.drawBody(e.x, e.y, e.r, e.hurt > 0 ? '#ffffff' : e.def.color, Math.atan2(hero.y - e.y, hero.x - e.x), '#ff3b2f');
      if (e.hp < e.maxHp) this.drawHpBar(e.x, e.y - e.r - 8, e.r * 2, e.hp / e.maxHp);
    }

    // Hero
    if (this.state !== 'dead') {
      this.drawBody(hero.x, hero.y, hero.r, hero.hurt > 0 ? '#ff9a8f' : hero.def.color, Math.atan2(hero.facing.y, hero.facing.x), '#f4f0e6');
    }

    // Projectiles
    for (const p of this.projectiles) {
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = p.team === 'hero' ? 12 : 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    // Effects
    for (const fx of this.effects) {
      const k = fx.t / fx.life;
      ctx.globalAlpha = 1 - k;
      ctx.strokeStyle = fx.color;
      ctx.fillStyle = fx.color;
      if (fx.type === 'arc') {
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(fx.x, fx.y, fx.range, fx.angle - fx.half, fx.angle + fx.half);
        ctx.stroke();
      } else if (fx.type === 'ring') {
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(fx.x, fx.y, fx.radius * (0.4 + 0.6 * k), 0, Math.PI * 2);
        ctx.stroke();
      } else if (fx.type === 'spark') {
        ctx.beginPath();
        ctx.arc(fx.x, fx.y, 3 + 10 * k, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;

    // Floating numbers
    ctx.font = 'bold 12px system-ui, sans-serif';
    ctx.textAlign = 'center';
    for (const f of this.floaters) {
      ctx.globalAlpha = 1 - f.t / 0.9;
      ctx.fillStyle = '#000';
      ctx.fillText(f.text, f.x + 1, f.y + 1);
      ctx.fillStyle = f.color;
      ctx.fillText(f.text, f.x, f.y);
    }
    ctx.globalAlpha = 1;

    // Torchlight vignette and touch stick, in screen space
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const cx = this.vw / 2;
    const cy = this.vh / 2;
    const light = ctx.createRadialGradient(cx, cy, 120 * zoom, cx, cy, Math.max(this.vw, this.vh) * 0.65);
    light.addColorStop(0, 'rgba(0,0,0,0)');
    light.addColorStop(1, 'rgba(0,0,0,0.85)');
    ctx.fillStyle = light;
    ctx.fillRect(0, 0, this.vw, this.vh);

    const st = this.input.stick;
    if (st) {
      ctx.strokeStyle = 'rgba(236,228,212,0.35)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(st.ox, st.oy, 50, 0, Math.PI * 2);
      ctx.stroke();
      const dx = st.x - st.ox;
      const dy = st.y - st.oy;
      const len = Math.min(50, Math.hypot(dx, dy));
      const ang = Math.atan2(dy, dx);
      ctx.fillStyle = 'rgba(236,228,212,0.45)';
      ctx.beginPath();
      ctx.arc(st.ox + Math.cos(ang) * len, st.oy + Math.sin(ang) * len, 22, 0, Math.PI * 2);
      ctx.fill();
    }

    this.ui.update(hero, this.abilities);
  }

  drawBody(x, y, r, color, angle, eyeColor) {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.beginPath();
    ctx.ellipse(x, y + r * 0.7, r, r * 0.45, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.5)';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.arc(x + Math.cos(angle) * r * 0.55, y + Math.sin(angle) * r * 0.55, Math.max(2, r * 0.2), 0, Math.PI * 2);
    ctx.fill();
  }

  drawHpBar(x, y, w, frac) {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(x - w / 2, y, w, 4);
    ctx.fillStyle = '#c23b32';
    ctx.fillRect(x - w / 2, y, w * Math.max(0, frac), 4);
  }
}
