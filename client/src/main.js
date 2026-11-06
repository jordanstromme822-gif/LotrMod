import { Game } from './game.js';
import { Input } from './input.js';

async function loadJSON(path) {
  const res = await fetch(path, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Could not load ${path} (${res.status})`);
  try {
    return await res.json();
  } catch (err) {
    throw new Error(`${path} is not valid JSON: ${err.message}`);
  }
}

const $ = (sel) => document.querySelector(sel);
const menu = $('#menu');
const overlay = $('#overlay');
const hud = $('#hud');
const abilityRoot = $('#abilities');
const bars = {
  hp: $('.bar.hp i'),
  hpText: $('.bar.hp span'),
  mana: $('.bar.mana i'),
  manaText: $('.bar.mana span'),
  xp: $('.bar.xp i'),
  xpText: $('.bar.xp span'),
};

const ui = {
  setAbilities(abilities) {
    const keys = ['1 / Click', '2', '3 / R-Click', '4'];
    abilityRoot.innerHTML = abilities
      .map((ab, i) => `<button type="button" class="ability" data-slot="${i}" title="${ab.name}"><span class="cd"></span><span class="key">${keys[i] ?? ''}</span><span class="name">${ab.name}</span></button>`)
      .join('');
    this.cdEls = [...abilityRoot.querySelectorAll('.cd')];
  },
  update(hero, abilities) {
    bars.hp.style.width = `${(hero.hp / hero.maxHp) * 100}%`;
    bars.hpText.textContent = `${Math.ceil(hero.hp)} / ${hero.maxHp}`;
    bars.mana.style.width = `${(hero.mana / hero.maxMana) * 100}%`;
    bars.manaText.textContent = `${Math.floor(hero.mana)} / ${hero.maxMana}`;
    bars.xp.style.width = `${(hero.xp / hero.xpNext) * 100}%`;
    bars.xpText.textContent = `Level ${hero.level}`;
    abilities.forEach((ab, i) => {
      const frac = ab.cooldown ? hero.cooldowns[i] / ab.cooldown : 0;
      this.cdEls[i]?.style.setProperty('--cd', frac.toFixed(3));
    });
  },
  showOverlay(title, text) {
    overlay.querySelector('h2').textContent = title;
    overlay.querySelector('p').textContent = text;
    overlay.hidden = false;
  },
};

function showError(err) {
  console.error(err);
  menu.innerHTML = `<h1>Something went wrong</h1><p class="tagline">${String(err.message).replace(/</g, '&lt;')}</p>`;
  menu.hidden = false;
}

try {
  const [heroes, abilities, enemies, dungeon] = await Promise.all([
    loadJSON('data/heroes.json'),
    loadJSON('data/abilities.json'),
    loadJSON('data/enemies.json'),
    loadJSON('data/dungeons/sunken-crypt.json'),
  ]);
  const input = new Input($('#game'), abilityRoot);
  const game = new Game({ canvas: $('#game'), input, data: { heroes, abilities, enemies, dungeon }, ui });
  window.game = game; // handy for testing mods from the browser console
  let heroId = heroes[0].id;

  $('#heroes').innerHTML = heroes
    .map((h) => `<button type="button" class="hero-card" data-id="${h.id}"><strong>${h.name}</strong><small>${h.description ?? ''}</small></button>`)
    .join('');
  $('#heroes').addEventListener('click', (e) => {
    const card = e.target.closest('.hero-card');
    if (!card) return;
    heroId = card.dataset.id;
    menu.hidden = true;
    hud.hidden = false;
    try {
      game.start(heroId);
    } catch (err) {
      hud.hidden = true;
      showError(err);
    }
  });
  overlay.querySelector('button').addEventListener('click', () => {
    overlay.hidden = true;
    game.start(heroId);
  });
} catch (err) {
  showError(err);
}
