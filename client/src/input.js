// Keyboard, mouse, and touch input. The game asks for a move direction,
// the aim point, and which ability slots are being held this frame.
const KEY_SLOTS = { Digit1: 0, Space: 0, Digit2: 1, Digit3: 2, Digit4: 3 };

export class Input {
  constructor(canvas, abilityRoot) {
    this.canvas = canvas;
    this.keys = new Set();
    this.held = new Set();
    this.mouse = { x: 0, y: 0, active: false };
    this.touchMode = matchMedia('(pointer: coarse)').matches;
    this.stick = null; // { id, ox, oy, x, y } in CSS pixels

    addEventListener('keydown', (e) => {
      this.keys.add(e.code);
      if (e.code in KEY_SLOTS) this.held.add(`k${KEY_SLOTS[e.code]}`);
      if (e.code === 'Space') e.preventDefault();
    });
    addEventListener('keyup', (e) => {
      this.keys.delete(e.code);
      if (e.code in KEY_SLOTS) this.held.delete(`k${KEY_SLOTS[e.code]}`);
    });
    addEventListener('blur', () => {
      this.keys.clear();
      this.held.clear();
      this.stick = null;
    });

    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    canvas.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'mouse') {
        this.touchMode = false;
        this.mouse.active = true;
        this.held.add(e.button === 2 ? 'm2' : 'm0');
        return;
      }
      this.touchMode = true;
      if (!this.stick && e.clientX < innerWidth * 0.6) {
        this.stick = { id: e.pointerId, ox: e.clientX, oy: e.clientY, x: e.clientX, y: e.clientY };
        try { canvas.setPointerCapture(e.pointerId); } catch {}
      }
    });
    canvas.addEventListener('pointermove', (e) => {
      if (e.pointerType === 'mouse') {
        this.mouse.x = e.clientX;
        this.mouse.y = e.clientY;
        this.mouse.active = true;
        this.touchMode = false;
      } else if (this.stick && e.pointerId === this.stick.id) {
        this.stick.x = e.clientX;
        this.stick.y = e.clientY;
      }
    });
    const release = (e) => {
      if (e.pointerType === 'mouse') this.held.delete(e.button === 2 ? 'm2' : 'm0');
      else if (this.stick && e.pointerId === this.stick.id) this.stick = null;
    };
    canvas.addEventListener('pointerup', release);
    canvas.addEventListener('pointercancel', release);

    // On-screen ability buttons work for both touch and mouse.
    abilityRoot.addEventListener('pointerdown', (e) => {
      const btn = e.target.closest('.ability');
      if (!btn) return;
      e.preventDefault();
      if (e.pointerType !== 'mouse') this.touchMode = true;
      try { btn.setPointerCapture(e.pointerId); } catch {}
      btn.classList.add('held');
      this.held.add(`b${btn.dataset.slot}`);
    });
    const btnUp = (e) => {
      const btn = e.target.closest('.ability');
      if (!btn) return;
      btn.classList.remove('held');
      this.held.delete(`b${btn.dataset.slot}`);
    };
    abilityRoot.addEventListener('pointerup', btnUp);
    abilityRoot.addEventListener('pointercancel', btnUp);
  }

  // Movement direction with length 0..1.
  move() {
    let x = 0;
    let y = 0;
    const k = this.keys;
    if (k.has('KeyA') || k.has('ArrowLeft')) x -= 1;
    if (k.has('KeyD') || k.has('ArrowRight')) x += 1;
    if (k.has('KeyW') || k.has('ArrowUp')) y -= 1;
    if (k.has('KeyS') || k.has('ArrowDown')) y += 1;
    if (this.stick) {
      const max = 50;
      x += (this.stick.x - this.stick.ox) / max;
      y += (this.stick.y - this.stick.oy) / max;
    }
    const len = Math.hypot(x, y);
    if (len > 1) return { x: x / len, y: y / len };
    if (len < 0.15) return { x: 0, y: 0 };
    return { x, y };
  }

  // Is ability slot n held by any input?
  slotHeld(n) {
    if (this.held.has(`k${n}`) || this.held.has(`b${n}`)) return true;
    if (n === 0 && this.held.has('m0')) return true;
    if (n === 2 && this.held.has('m2')) return true;
    return false;
  }
}
