      // Story map (Jordan, 2026-11-09): every hero's story as a grid, left to right, one block per screen. Screens two
      // heroes both walk sit once in the empty row between them. Read from the game: mission starts (path table
      // 0x08283030), each screen's exits (spawn records of type 3, level byte at +0x13) and the story scenes.
      window.StoryMap = (() => {
        const NAMES = ["Anduin Banks","Campsite","Corsair Camp","Corsair Chase","Top Room","Tower","Ambush","Cirith Campsite","Ledge","Parapet","Pass","Lair Campsite","Stairs","Summit","Above","Below","Crack of Doom","Edge of Volcano","Tunnel","Campsite","Dwimerberg Base","Dwimerberg Mt.","Glen","Road","Anduin Docks","Minas Tirith Docks","Campsite","Foot of Mt Doom","Sammath Naur","Slopes of Mt Doom","Camps","Campsite","Hills","Hollow","Plateau","River Crossing","Campsite","Clearing","Copse","Entwash","Campsite","Hills","Orc Road","Plains","Campsite","Caverns","Fortress","Valley","Ice Caves","Balin's Tomb","Campsite","Flooded Field","Uruk Hatchery","Orthanc","Orthanc Tunnel","Tower Base","Tower Door","Tower Levels","Black Gate","Black Road","North","Waterfall","Battlements","Court of Kings","Gates","City Center","Streets","Steward's Tomb","Denethor Fall","Gates","Minas City Center","Streets","Tier Four","Tier Three","Bridge","Campsite","Crossroads","Gate","Minas Morgul","Vale of Morgul","Valley","Hall","Hall Top","Long Stairs","Treasure Hoards","Black Chasm","Campsite","Dark Paths","Grey Vapors","Secret Cave","West Beacon","East Beacon","Minas Entrance","Edge","Fall of Rohirrim","North Fields","Hidden Plains","West Fields","Witch King","Mumakil Attack","Campsite","Theoden's Charge","Footpath","Fork","Haradrim Camp","Mt. Mindolluin","Mumakil Camp","Outpost","Campsite","Edoras Fields","Gap","Deeping Outskirts","Hills","Plains","Snowbourne Trail","Caves","Lair","Tunnel Mouth","Campsite","Hills","Marsh","Tower","Approach","Campsite","Edge","Foothills","Narrow Pass","SE Mts. Edge","Hidden Trail","Storm"];
        const REG = [[0,3,"Anduin River"],[4,5,"Orc Tower"],[6,13,"Cirith Ungol"],[14,15,"Corsair Flagship"],[16,18,"Crack of Doom"],[19,23,"Dimholt"],[24,25,"Docks"],[26,29,"Mt Doom"],[30,35,"Dunharrow"],[36,39,"Entwood"],[40,43,"Gorgoroth"],[44,47,"Hornburg"],[48,49,"Ice Cave"],[50,57,"Isengard"],[58,61,"Ithilien"],[62,67,"Minas Tirith"],[68,68,"Balcony"],[69,73,"Minas Tirith"],[74,80,"Morgul"],[81,84,"Dwarf Halls"],[85,89,"Paths of the Dead"],[90,92,"Pelennor Beacon"],[93,98,"Pelennor Battle"],[99,107,"Pelennor Fields"],[108,114,"Rohan"],[115,117,"Shelob's Lair"],[118,121,"Amon Sul"],[122,129,"White Mountains"]];
        const region = (l) => { for (const r of REG) if (l >= r[0] && l <= r[1]) return r[2]; return ""; };
        // Each hero's missions in story order (Legolas and Gimli walk Aragorn's path, Sam walks Frodo's).
        const HEROES = [
          { name: "Gandalf", sub: "", m: [[51,55,54,52,56,57,53,50],[113,114,111,112,108],[128,126,122,123],[97,105,103,90,91,95,100],[69,73,72,71,63,67,68,60,61,59,58]] },
          { name: "Aragorn", sub: "+ Legolas, Gimli", m: [[51,55,54,52,56,57,53,50],[32,34,30,31,23,20,21,19,22],[88,87,85,86],[2,3,0,1,24,15,14],[25,107,102,92,60,61,59,58]] },
          { name: "Éowyn", sub: "", m: [[109,110,112,108],[32,34,30,31],[125,129,48,124,127,123],[93,104,96,106,100,101],[99,94,98]] },
          { name: "Frodo", sub: "+ Sam", m: [[79,76,78,77,89,74,80,75,12,8,13,10],[117,115,116],[6,9,5,4,7,42,43,41,40],[27,29,28,26],[18,16,17]] },
        ];
        // Big story fights (the scene after them, or the fight the level is named for).
        const BOSS = { 53: "Saruman", 85: "Army of the Dead", 14: "Corsair flagship", 58: "Last stand", 98: "Witch-king", 116: "Shelob", 4: "Orc Tower", 17: "Gollum" };
        // Screens with reward side-quest dialogue (dialogue ids 21, 28-30, 33, 37, 48-53 found in their scripts).
        const SIDE = { 30: 1, 1: 1, 2: 1, 61: 1, 111: 1, 109: 1 };
        // More Orc Heads there (Play Room v120): Black Gate and Cirith Ungol on Hard, Pelennor Fields on Grueling.
        const orc = (l) => l === 58 || (l >= 6 && l <= 13) ? "Hard" : l >= 99 && l <= 107 ? "Grueling" : "";
        function layout() {
          // Column = one more than the latest screen before it on every hero's path that walks it.
          const who = {}, first = {}; let seq = HEROES.map((h, hi) => { const s = []; h.m.forEach((ms, mi) => ms.forEach((l, k) => { s.push(l); (who[l] = who[l] || new Set()).add(hi); if (!k) (first[hi] = first[hi] || {})[l] = mi + 1; })); return s; });
          const col = {}; for (let it = 0; it < 200; it++) { let ch = false; seq.forEach((s) => s.forEach((l, i) => { const c = i ? col[s[i - 1]] + 1 : 0; if (!(col[l] >= c)) { col[l] = c; ch = true; } })); if (!ch) break; }
          const cells = {}, key = (r, c) => r + ":" + c;
          // Hero h is on row 2h; the empty row between heroes a and a+1 is 2a+1.
          const shared = [];
          Object.keys(col).forEach((k) => { const l = +k, hs = [...who[l]].sort(); if (hs.length === 1) cells[key(2 * hs[0], col[l])] = { l, hs }; else shared.push({ l, hs }); });
          shared.forEach((s) => {
            const lo = s.hs[0], hi = s.hs[s.hs.length - 1], c = col[s.l];
            const opts = []; for (let g = lo; g < hi; g++) opts.push(2 * g + 1);
            opts.sort((a, b) => Math.abs(a - (lo + hi)) - Math.abs(b - (lo + hi)));
            const r = opts.find((r) => !cells[key(r, c)]) || opts[0];
            cells[key(r, c)] = { l: s.l, hs: s.hs };
            s.hs.forEach((h) => { if (!cells[key(2 * h, c)]) cells[key(2 * h, c)] = { arrow: r < 2 * h ? "up" : "down" }; });
          });
          return { cells, cols: Math.max(...Object.values(col)) + 1, rows: HEROES.length * 2 - 1, first };
        }
        let el = null;
        function render() {
          const L = layout(), box = document.createElement("div"); box.id = "storyMap";
          const top = document.createElement("div"); top.className = "sm-top";
          top.innerHTML = '<div class="sm-title">Story map</div><div class="sm-leg"><span><b class="n"></b>Screen</span><span><b class="boss"></b>Big fight</span><span><b class="side"></b>Side quest</span><span><b class="team"></b>Team-up (both heroes walk it)</span><span><b class="n orc"></b>More Orc Heads</span></div>';
          const x = document.createElement("button"); x.type = "button"; x.className = "sm-close"; x.textContent = "Close"; x.addEventListener("click", (e) => { e.preventDefault(); close(); }); top.appendChild(x);
          box.appendChild(top);
          const sc = document.createElement("div"); sc.className = "sm-scroll"; box.appendChild(sc);
          const g = document.createElement("div"); g.className = "sm-grid"; g.style.gridTemplateColumns = "112px repeat(" + L.cols + ", 92px)"; sc.appendChild(g);
          for (let r = 0; r < L.rows; r++) {
            const head = document.createElement("div"); head.className = r % 2 ? "sm-gaphead" : "sm-hero";
            if (!(r % 2)) { const h = HEROES[r / 2]; head.innerHTML = h.name + (h.sub ? "<span>" + h.sub + "</span>" : ""); }
            g.appendChild(head);
            for (let c = 0; c < L.cols; c++) {
              const d = document.createElement("div"), v = L.cells[r + ":" + c];
              if (!v) { d.className = "sm-empty"; g.appendChild(d); continue; }
              if (v.arrow) { d.className = "sm-arrow"; d.textContent = v.arrow === "up" ? "▲" : "▼"; g.appendChild(d); continue; }
              const l = v.l, team = v.hs.length > 1, o = orc(l);
              d.className = "sm-b " + (BOSS[l] ? "boss" : SIDE[l] ? "side" : team ? "team" : "n") + (team && (BOSS[l] || SIDE[l]) ? " teamedge" : "") + (o ? " orc" : "");
              const mi = v.hs.map((h) => L.first[h] && L.first[h][l]).find((m) => m);
              let t = (mi ? '<i class="sm-m">Mission ' + mi + "</i>" : "") + "<b>" + NAMES[l] + "</b>";
              const rg = region(l); if (NAMES[l].indexOf("Camp") === 0 || NAMES[l] === "Hills" || NAMES[l] === "Edge" || NAMES[l] === "Gates" || NAMES[l] === "Streets" || NAMES[l] === "Valley" || NAMES[l] === "Plains" || NAMES[l] === "Tower") t += "<i>" + rg + "</i>";
              if (BOSS[l]) t += "<i>" + BOSS[l] + "</i>";
              if (team) t += "<i>" + v.hs.map((h) => HEROES[h].name).join(" + ") + "</i>";
              if (o) t += '<u>Orc Heads: ' + o + "</u>";
              d.innerHTML = t; d.title = NAMES[l] + " (" + rg + ", level " + l + ")"; g.appendChild(d);
            }
          }
          const foot = document.createElement("div"); foot.className = "sm-foot";
          foot.textContent = "Read from the game: where each mission starts, which screen each exit leads to, and the story scenes. Red marks are my reading of the story scenes; a few side screens the story never walks through are left out.";
          sc.appendChild(foot);
          return box;
        }
        function open() { if (el) return; el = render(); document.body.appendChild(el); }
        function close() { if (el) { el.remove(); el = null; } }
        return { open, close, layout, isOpen: () => !!el };
      })();
