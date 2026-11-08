// Play Room v114: Undo (sold or thrown-away items, skill points). Cut from the page.
      // Leaving the screen the item went from (back to play, or to the Skills or Attributes tab) forgets it (Jordan, 2026-11-08).
      let undoList = [], undoSnap = null, undoSt = -1, undoFlipT = 0;
      const u32 = (h, o) => (h[o] | h[o + 1] << 8 | h[o + 2] << 16 | h[o + 3] << 24) >>> 0;
      const undoRead = () => { const h = emu.Module.HEAPU8, P = heroPtr(), it = []; for (let k = 0; k < 16; k++) it.push(u32(h, P + 0x3C + 4 * k)); return { P, it, gems: h[P + 0x184] | h[P + 0x185] << 8 }; };
      const undoNote = (msg) => { const n = $("saveNote"); if (!n) return; n.textContent = msg; n.hidden = false; clearTimeout(undoNote.t); undoNote.t = setTimeout(() => { n.hidden = true; }, 2200); };
      setInterval(() => {
        if (iwram < 0 || linked()) { undoList = []; undoSnap = null; return; }
        const st = gameState();
        if (performance.now() < undoFlipT) return;   // the page's own redraw flip (Backpack -> next tab -> Backpack)
        if (st !== undoSt) { undoList = []; undoSnap = null; undoSt = st; }
        if (st === 1 || st === 5 || st === 2 || st === 3 || st === 16) { $("qsBtn").classList.remove("can"); return; }
        let cur; try { cur = undoRead(); } catch (e) { return; }
        if (undoSnap && undoSnap.P === cur.P) {
          const left = cur.it.slice(), gone = [];
          undoSnap.it.forEach((w, k) => { if ((w & 15) === 15) return; const j = left.indexOf(w); if (j >= 0) left[j] = -1; else gone.push([k, w]); });
          const g = cur.gems - undoSnap.gems;
          gone.forEach(([k, w], i) => undoList.push({ k, w, gems: i === 0 && g > 0 ? g : 0 }));
          if (undoList.length > 20) undoList.shift();
        }
        undoSnap = cur;
        $("qsBtn").classList.toggle("can", undoList.length > 0 || inSkillsTab());
      }, 60);
      const undoItem = () => {
        const u = undoList[undoList.length - 1]; if (!u) return false;
        const h = emu.Module.HEAPU8, P = heroPtr();
        let at = u.k >= 8 ? P + 0x3C + 4 * u.k : -1;
        if (at < 0 || (u32(h, at) & 15) !== 15) { at = -1; for (let k = 0; k < 8; k++) { const o = P + 0x5C + 4 * k; if ((u32(h, o) & 15) === 15) { at = o; break; } } }
        if (at < 0) { undoNote("No room in the backpack to bring it back."); return true; }
        const gems = h[P + 0x184] | h[P + 0x185] << 8;
        if (u.gems > gems) { undoNote("Not enough gems left to take the sale back."); return true; }
        undoList.pop();
        for (let b = 0; b < 4; b++) h[at + b] = (u.w >>> (8 * b)) & 255;
        const ng = gems - u.gems; h[P + 0x184] = ng & 255; h[P + 0x185] = ng >> 8;
        try { if (window.__mirrorIw) { for (let b = 0; b < 4; b++) window.__mirrorIw(at - iwram + b); window.__mirrorIw(P + 0x184 - iwram); window.__mirrorIw(P + 0x185 - iwram); } } catch (e) {}
        undoSnap = undoRead();
        // The Backpack screen only redraws its items when it is opened, so the page flips to the next tab and back while
        // the picture stays still and the sound is off (Jordan, 2026-11-08: the flip showed). The list is kept meanwhile.
        if (gameState() === 0x0A) {
          const gi = (k, on) => { try { emu.gameManager.simulateInput(0, k, on); } catch (e) {} };
          undoFlipT = performance.now() + 1500; try { window.__wideHold && window.__wideHold(1500); } catch (e) {}
          gi(11, 1); setTimeout(() => gi(11, 0), 90); setTimeout(() => gi(10, 1), 750); setTimeout(() => { gi(10, 0); sendL(); }, 840);
          setTimeout(() => { undoSnap = undoRead(); undoSt = gameState(); }, 1450);
        } else if (gameState() === 20) {
          // Shrine / shop (Jordan, 2026-11-08: a sold item came back but didn't show): the shop only draws the backpack and
          // gems when it opens, so the page closes it (B) and opens it again (Grab) behind a still picture.
          const gi = (k, on) => { try { emu.gameManager.simulateInput(0, k, on); } catch (e) {} };
          undoFlipT = performance.now() + 2200; try { window.__wideHold && window.__wideHold(1900); } catch (e) {}
          gi(0, 1); setTimeout(() => gi(0, 0), 100);
          [700, 1000, 1300, 1600].forEach((t) => setTimeout(() => { if (gameState() === 1 && window.__grab) { window.__grab(1); setTimeout(() => window.__grab(0), 120); } }, t));
          setTimeout(() => { undoSnap = undoRead(); undoSt = gameState(); }, 2150);
        }
        undoNote(u.gems ? "Sale taken back (" + u.gems + " gems)." : "Item brought back.");
        return true;
      };
      const undo = () => {
        if (inSkillsTab()) { refundPulse(); return; }
        if (!inMenu() || !undoItem()) return;
        $("qsBtn").classList.add("on"); setTimeout(() => $("qsBtn").classList.remove("on"), 140);
      };
      window.__undo = undo;
