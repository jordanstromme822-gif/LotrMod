// Play Room v115: what the Grab button reads (Open / Full / Grab). Cut from the page (Auto scope).
        // For the Grab button's label: an unopened chest or the Shrine within reach (Open), a full backpack (Full).
        window.__grabInfo = () => {
          try {
            if (iwram < 0 || inMenu()) return null;
            ew = findEw(); H8 = heap(); if (ew < 0) return null;
            const P = playerAddr(), hero = r32(P); if (hero >>> 24 !== 2) return null;
            const [x, y] = pos(hero); let open = false, item = null, itemD = 1e9;
            for (const p of entities()) {
              const u = r32(p + 0x14);
              if (u === CHEST_UPD && !r8(p + 0x85)) { const [bx, by] = pos(p); if (bx - x >= -18 && bx - x <= 22 && Math.abs(by - y) <= 24) { open = true; break; } }
              else if (u === SHOP_UPD) { const [sx, sy] = pos(p); if (Math.abs(sx - x) <= 30 && Math.abs(sy - y) <= 30) { open = true; break; } }
              else if (u === ITEM_UPD && r8(p + 0x63) === 3) { const [ix, iy] = pos(p), d = Math.max(Math.abs(ix - x), Math.abs(iy - y)); if (d <= 22 && d < itemD) { itemD = d; item = p; } }
            }
            // Standing over something (Jordan, 2026-11-08): Grab if it can be taken, Full if not: food only when hurt,
            // herbs unless both herb pouches are full (10 each), gear only with backpack room.
            let full = packFull(P);
            if (item) {
              const t = r8(item + 0x60), hb = r8(P + 0x1AA);
              full = t === 15 || t === 16 || t === 19 ? r16(P + 0x17C) >= r16(P + 0xD0) : t >= 25 ? packFull(P) : t >= 17 ? (hb >> 4) >= 10 && (hb & 15) >= 10 : false;
            }
            return { open, full };
          } catch (e) { return null; }
        };
