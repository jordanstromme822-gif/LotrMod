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
        // Enemies placed on each screen (Jordan, 2026-11-09): [small, medium, large, boss, spawners]. Size from the kind's
        // hit points (stats table 0x08057518 + 6): small under 40, medium under 150, large 150 and up (trolls, oliphaunts);
        // boss = the one-off story fights. Spawners keep making more enemies, so those screens have more than this.
        const COUNTS = {"51":[12,0,0,0,0],"55":[2,1,0,0,0],"54":[15,1,0,0,0],"52":[12,3,0,0,0],"56":[0,3,0,0,0],"57":[0,1,0,0,0],"53":[2,1,0,0,1],"50":[0,0,0,0,0],"113":[13,0,0,0,0],"114":[27,5,0,0,4],"111":[11,17,0,0,1],"112":[38,4,0,0,0],"108":[3,0,0,0,0],"128":[20,1,1,0,2],"126":[11,0,0,0,0],"122":[3,0,2,0,3],"123":[0,0,0,0,0],"97":[18,7,0,0,0],"105":[19,19,0,1,0],"103":[17,7,0,0,1],"90":[12,13,0,0,0],"91":[16,1,0,0,0],"95":[14,13,0,0,10],"100":[0,0,0,0,0],"69":[5,10,5,1,0],"73":[16,19,0,0,0],"72":[0,1,0,1,0],"71":[0,0,0,0,0],"63":[0,0,0,0,0],"67":[0,0,0,1,0],"68":[0,0,0,0,0],"60":[12,40,9,0,1],"61":[0,0,0,0,1],"59":[19,32,3,0,0],"58":[34,17,2,0,0],"32":[44,6,0,0,0],"34":[21,3,0,0,0],"30":[16,8,1,0,4],"31":[0,0,0,0,0],"23":[13,9,0,0,0],"20":[17,11,3,0,0],"21":[52,3,0,0,2],"19":[5,0,0,0,0],"22":[42,7,0,0,2],"88":[96,0,0,0,0],"87":[59,0,0,0,0],"85":[39,0,0,1,1],"86":[9,0,0,0,0],"2":[0,20,1,0,1],"3":[0,23,4,0,0],"0":[23,19,3,0,1],"1":[0,0,0,0,0],"24":[0,13,1,0,0],"15":[0,3,1,0,0],"14":[9,8,1,1,0],"25":[16,15,1,0,0],"107":[24,25,0,0,0],"102":[29,12,0,0,6],"92":[1,8,0,0,1],"109":[26,0,0,0,0],"110":[21,2,0,0,6],"125":[46,7,1,0,0],"129":[18,1,0,0,0],"48":[5,8,2,0,0],"124":[15,11,0,0,0],"127":[35,3,0,0,1],"93":[16,20,1,0,0],"104":[7,12,0,0,0],"96":[4,0,1,0,0],"106":[0,6,7,0,1],"101":[6,2,0,0,0],"99":[0,1,8,0,0],"94":[3,0,2,0,0],"98":[0,0,0,1,1],"79":[13,0,0,0,0],"76":[24,0,0,0,0],"78":[29,9,0,0,0],"77":[5,3,0,0,0],"89":[0,0,0,0,0],"74":[9,2,0,0,0],"80":[18,2,0,0,0],"75":[1,0,0,0,0],"12":[19,2,0,0,0],"8":[12,0,0,0,0],"13":[30,9,2,0,5],"10":[30,1,0,0,0],"117":[44,4,0,0,6],"115":[44,5,0,0,3],"116":[62,6,0,1,3],"6":[4,10,0,1,4],"9":[9,12,0,0,0],"5":[9,6,0,0,0],"4":[2,0,1,0,7],"7":[1,0,0,0,7],"42":[14,10,0,0,0],"43":[42,1,0,0,0],"41":[27,0,1,0,0],"40":[3,1,0,0,0],"27":[5,7,0,0,0],"29":[9,7,2,0,1],"28":[9,1,1,0,0],"26":[2,0,1,0,0],"18":[10,0,0,0,3],"16":[36,1,3,0,0],"17":[2,0,1,0,0],"82":[26,13,0,0,0],"83":[12,15,0,0,0],"84":[42,15,5,0,13],"81":[60,3,2,0,19],"49":[5,2,1,0,6],"121":[0,6,0,0,0],"46":[3,10,1,0,0],"47":[4,27,3,0,1],"37":[34,38,17,0,0],"38":[48,12,3,0,0],"39":[40,38,14,0,0],"36":[17,2,8,0,0]};
        const cnt = (l) => {
          const c = COUNTS[l]; if (!c) return "";
          const rows = [["Boss", c[3]], ["Large", c[2]], ["Medium", c[1]], ["Small", c[0]]].filter((x) => x[1]);
          const tot = c[0] + c[1] + c[2] + c[3];
          if (!rows.length && !c[4]) return "";
          let h = '<span class="sm-cnt">' + rows.map((x) => "<span><em>" + x[0] + "</em><em>" + x[1] + "</em></span>").join("");
          if (rows.length) h += '<span class="sm-tot"><em>Total</em><em>' + tot + "</em></span>";
          if (c[4]) h += '<span class="sm-sp"><em>Spawners</em><em>' + c[4] + "</em></span>";
          return h + "</span>";
        };
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
        // Bonus maps (Jordan, 2026-11-09): each map's screens in order, with its big monsters. Screens from the exits;
        // monsters from the live enemies' kind (+0x61) and hit points (stats table 0x08057518, 20 bytes per kind, +6).
        const BONUS = [
          { name: "Moria", s: [[82], [83], [84, "Trolls", "250 HP each"], [81], [49, "Cave troll", "350 HP"]] },
          { name: "Amon Sûl", s: [[121, "Ringwraiths", "by the fire"]] },
          { name: "Hornburg", s: [[46], [47]] },
          { name: "Entwood", s: [[37], [38], [39], [36, "Troll", "525 HP"]] },
        ];
        let tab = "story";
        // Siege layout (Jordan, 2026-11-10): pick which existing screen goes in each of the 8 Siege spots. Helm's Deep is the
        // fixed start at the bottom. Walk time = the long side of the screen at the hero's walking speed (1.5 pixels a frame,
        // 90 a second, measured on Hornburg Valley), so real paths with turns take longer.
        const WALK = {"0":21,"1":5,"2":17,"3":20,"4":9,"5":11,"6":16,"7":11,"8":9,"9":11,"10":15,"12":16,"13":27,"14":6,"15":6,"16":18,"17":12,"18":14,"19":5,"20":12,"21":17,"22":15,"23":14,"24":6,"25":12,"26":5,"27":14,"28":14,"29":20,"30":9,"31":5,"32":20,"34":12,"36":5,"37":21,"38":18,"39":18,"40":7,"41":23,"42":21,"43":9,"46":17,"47":9,"48":22,"49":13,"50":9,"51":14,"52":20,"53":14,"54":9,"55":9,"56":5,"57":25,"58":14,"59":23,"60":18,"61":6,"63":11,"67":9,"68":3,"69":18,"71":17,"72":11,"73":13,"74":14,"75":5,"76":11,"77":18,"78":21,"79":11,"80":18,"81":20,"82":23,"83":19,"84":23,"85":11,"86":9,"87":16,"88":18,"89":15,"90":10,"91":10,"92":14,"93":13,"94":11,"95":17,"96":9,"97":14,"98":5,"99":16,"100":5,"101":15,"102":12,"103":11,"104":18,"105":23,"106":21,"107":12,"108":5,"109":7,"110":23,"111":12,"112":14,"113":11,"114":24,"115":16,"116":22,"117":22,"121":8,"122":21,"123":5,"124":13,"125":11,"126":28,"127":13,"128":14,"129":9};
        // 5 x 5 Siege grid (Jordan, 2026-11-10): rows A (top) to E (bottom), columns 1-5. Helm's Deep is fixed at E3.
        const SLOTS = [];
        for (let r = 1; r <= 5; r++) for (let c = 1; c <= 5; c++) SLOTS.push({ k: "r" + r + "c" + c, n: "ABCDE"[r - 1] + c, r, c });
        const SPECIAL = { r1c3: "Black Gate", r4c3: "Outer Gate approach", r5c3: "Helm's Deep (start)" };
        SLOTS.forEach((t) => { if (SPECIAL[t.k]) t.n = t.n + " · " + SPECIAL[t.k]; if (t.k === "r5c3") t.fixed = 46; });
        const OLD = { nw: "r2c2", bg: "r1c3", ne: "r2c4", mid: "r3c3", sw: "r4c2", app: "r4c3", se: "r4c4" };
        const DEF = { r1c3: 58, r4c3: 47, r5c3: 46 };
        const fixSlots = (v) => { const o = Object.assign({}, DEF); Object.keys(v || {}).forEach((k) => { const nk = OLD[k] || k; if (/^r[1-5]c[1-5]$/.test(nk) && typeof v[k] === "number") o[nk] = v[k]; }); o.r5c3 = 46; return o; };
        // Screens grouped by how they look (sorted by eye from the overhead pictures).
        const LOOK = [["Woods", [19, 20, 21, 22, 23, 36, 37, 38, 59, 60]], ["Plains", [92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 109, 110, 112, 114]], ["River & water", [0, 2, 3, 39]], ["Ships & docks", [14, 15, 24, 25]], ["Camps & houses", [1, 61, 108, 111, 113]], ["Snow & ice", [48, 122, 123, 124, 125, 126, 127, 128, 129]], ["Lava", [16, 17, 18, 28, 29, 42]], ["Wasteland", [26, 27, 40, 41, 43, 50, 51]], ["Mountains", [6, 7, 8, 10, 12, 13, 74, 75, 76, 77, 78, 79, 80]], ["Red rock", [30, 31, 32, 34]], ["Fortress", [4, 5, 9, 46, 47, 53, 55, 56, 57, 58]], ["City", [63, 67, 68, 69, 71, 72, 73, 90, 91]], ["Dwarf halls", [49, 81, 82, 83, 84]], ["Caves", [52, 54, 85, 86, 87, 88, 89, 115, 116, 117]], ["Ruins", [121]]];
        let look = 0;
        let siege = fixSlots({}), sel = "r2c2";
        try { const v = JSON.parse(localStorage.getItem("rotk-siege") || "null"); if (v && typeof v === "object") siege = fixSlots(v); } catch (e) {}
        const siegeDb = (async () => { const use = window.claude && window.claude.use; if (!use) return null; const [db, user] = await Promise.all([use("db"), use("user")]); const id = db && user && await user.id(); return id ? db.doc("data/users/" + id + "/siege-layout") : null; })().catch(() => null);
        try { const v = JSON.parse(localStorage.getItem("rotk-siege-tf") || "null"); if (v && typeof v === "object") tfs = v; } catch (e) {}
        let siegeLoaded = false, siegeRedraw = null;
        function siegeLoad() {
          if (siegeLoaded) return; siegeLoaded = true;
          siegeDb.then((d) => d && d.get()).then((r) => { if (r && r.exists) { const v = r.data(); if (v && v.slots) { siege = fixSlots(v.slots); tfs = v.tf && typeof v.tf === "object" ? v.tf : {}; try { localStorage.setItem("rotk-siege", JSON.stringify(siege)); } catch (e) {} if (siegeRedraw) siegeRedraw(); } } }).catch(() => {});
        }
        let saveT = 0;
        function siegeSave(msg) {
          try { localStorage.setItem("rotk-siege", JSON.stringify(siege)); localStorage.setItem("rotk-siege-tf", JSON.stringify(tfs)); } catch (e) {}
          clearTimeout(saveT); msg.textContent = "Saving…";
          saveT = setTimeout(() => siegeDb.then((d) => { if (!d) { msg.textContent = "Saved on this device."; return; } return d.set({ slots: siege, tf: tfs, at: Date.now() }).then(() => { msg.textContent = "Saved to your account."; }); }).catch(() => { msg.textContent = "Saved on this device (account save failed)."; }), 600);
        }
        // Picture size and where you come in (0, green) and the exits (1, red; 4th value = level it leads to), in thousandths
        // of the picture. Read by walking the hero onto every exit (tools/storymap/ent.py) plus each level's start point.
        const SZ = {"0":[1920,1704],"1":[480,456],"2":[1504,840],"3":[1792,680],"4":[800,776],"5":[1024,936],"6":[1408,616],"7":[960,648],"8":[640,840],"9":[960,872],"10":[1344,1224],"12":[640,1416],"13":[2400,456],"14":[576,552],"15":[576,552],"16":[1600,1160],"17":[1120,776],"18":[672,1288],"19":[480,456],"20":[800,1064],"21":[1216,1544],"22":[1344,776],"23":[704,1256],"24":[512,488],"25":[1056,616],"26":[480,456],"27":[1024,1224],"28":[672,1224],"29":[1824,840],"30":[800,691],"31":[480,456],"32":[1760,552],"34":[800,1096],"36":[480,456],"37":[1856,1576],"38":[1600,1576],"39":[1536,1608],"40":[480,616],"41":[2048,520],"42":[1920,1224],"43":[608,776],"46":[1536,776],"47":[800,776],"48":[1952,2024],"49":[960,1192],"50":[800,808],"51":[1152,1256],"52":[896,1800],"53":[1248,744],"54":[736,808],"55":[800,616],"56":[448,424],"57":[2240,456],"58":[800,1256],"59":[800,2056],"60":[1600,872],"61":[512,323],"63":[1024,488],"67":[704,776],"68":[240,136],"69":[800,1576],"71":[1504,808],"72":[960,936],"73":[1120,1128],"74":[1088,1224],"75":[480,456],"76":[1024,1032],"77":[1248,1576],"78":[1920,712],"79":[1024,776],"80":[1632,1000],"81":[1184,1768],"82":[2048,1384],"83":[800,1736],"84":[2048,1608],"85":[960,456],"86":[480,776],"87":[1440,1064],"88":[1024,1576],"89":[608,1320],"90":[800,936],"91":[800,936],"92":[800,1256],"93":[1152,776],"94":[960,680],"95":[1504,1032],"96":[832,328],"97":[1280,936],"98":[480,456],"99":[1440,1320],"100":[480,456],"101":[640,1320],"102":[800,1096],"103":[1024,680],"104":[1600,1576],"105":[2048,1512],"106":[1920,808],"107":[1120,1096],"108":[480,488],"109":[672,616],"110":[2048,584],"111":[1056,904],"112":[1248,776],"113":[960,712],"114":[2144,872],"115":[1440,1288],"116":[800,2024],"117":[1600,2024],"121":[480,712],"122":[1920,680],"123":[480,392],"124":[1152,1064],"125":[800,1032],"126":[2560,488],"127":[704,1128],"128":[1152,1256],"129":[800,776]};
        const EE = {"0":[[0,875,1000],[1,108,12,1]],"1":[[0,967,886],[1,33,445,24]],"2":[[0,17,825],[1,988,35,3]],"3":[[0,973,985],[1,107,16,0]],"4":[[0,396,287],[1,401,291,7]],"5":[[0,154,1000],[1,809,67,4]],"6":[[0,717,508],[0,26,437],[1,717,508,6]],"7":[[0,903,136],[1,4,878,42]],"8":[[0,42,1000],[1,498,785,13],[1,978,271,10]],"9":[[0,22,822],[1,277,108,5]],"10":[[0,20,955],[1,768,404,117]],"12":[[0,297,1000],[1,988,52,8]],"13":[[0,675,838],[0,252,750],[0,35,958],[1,998,375,6],[1,674,706,8],[1,247,561,117]],"14":[[0,167,158],[1,970,1000,25]],"15":[[0,292,817],[1,135,114,14]],"16":[[0,402,994],[1,248,35,17],[1,747,27,17],[1,541,11,17]],"17":[[0,135,184]],"18":[[0,452,1000],[1,814,28,16]],"19":[[0,850,950],[1,15,88,22]],"20":[[0,969,969],[1,16,68,21]],"21":[[0,980,965],[1,10,93,19]],"22":[[0,977,122],[1,38,809,88]],"23":[[0,53,123],[1,18,955,20]],"24":[[0,963,834],[1,453,227,15]],"25":[[0,122,273],[1,994,727,107]],"26":[[0,92,226],[1,950,1000,18]],"27":[[0,38,895],[1,233,17,29]],"28":[[0,73,934],[1,981,424,26]],"29":[[0,329,1000],[1,997,568,28],[1,997,674,28]],"30":[[0,30,1000]],"31":[[0,67,169],[1,973,660,125]],"32":[[0,18,926],[1,997,178,34]],"34":[[0,69,201],[1,994,976,30]],"36":[[0,52,55],[1,952,989,0]],"37":[[0,10,969],[1,985,36,38]],"38":[[0,13,936],[1,996,179,39]],"39":[[0,117,51],[1,997,751,36]],"40":[[0,162,750],[1,969,390,27]],"41":[[0,19,767],[1,992,615,40]],"42":[[0,42,514],[1,989,523,43]],"43":[[0,104,39],[1,975,858,41]],"46":[[0,147,183]],"47":[[0,42,45],[1,42,52,0]],"48":[[0,99,28],[1,119,1000,124]],"49":[[0,926,948],[0,331,86],[1,332,81,49]],"50":[[0,51,954],[1,982,64,0]],"51":[[0,30,888],[1,493,4,55]],"52":[[0,964,905],[1,992,46,56]],"53":[[0,190,355],[1,802,255,50]],"54":[[0,935,335],[1,73,35,52]],"55":[[0,430,1000],[1,154,833,54]],"56":[[0,51,851],[1,654,134,57]],"57":[[0,179,671]],"58":[[0,56,949],[1,831,212,0]],"59":[[0,396,1000],[1,555,6,58]],"60":[[0,299,97],[0,16,417],[1,988,1000,59],[1,270,30,61]],"61":[[0,656,1000],[1,807,1000,60]],"63":[[0,23,555],[0,922,549],[1,5,609,0]],"67":[[0,297,376]],"68":[[1,21,1000,0]],"69":[[0,70,962],[1,982,395,73]],"71":[[0,58,870],[1,987,153,63]],"72":[[0,150,884],[1,844,99,71]],"73":[[0,41,880],[1,724,93,72]],"74":[[0,503,233],[0,75,145],[1,984,868,80]],"75":[[0,75,461],[1,973,557,12]],"76":[[0,56,181],[1,787,1000,78]],"77":[[0,895,972],[1,967,129,89],[1,962,450,74]],"78":[[0,11,132],[1,448,21,77]],"79":[[0,29,727],[1,987,660,76]],"80":[[0,12,55],[1,989,547,75]],"81":[[0,205,64],[1,940,870,49]],"82":[[0,946,212],[1,43,167,83]],"83":[[0,94,36],[1,959,897,84]],"84":[[0,21,35],[1,995,743,81]],"85":[[0,14,811],[1,775,384,86]],"86":[[0,81,76],[1,10,934,125]],"87":[[0,68,799],[1,959,43,85]],"88":[[0,85,84],[1,967,1000,87]],"89":[[0,158,89],[1,947,895,74]],"90":[[0,524,1000],[1,451,983,103],[1,326,892,95]],"91":[[0,479,965],[1,665,902,103]],"92":[[0,25,982],[1,468,231,60]],"93":[[0,102,643],[1,991,494,104]],"94":[[0,31,118],[1,942,991,98]],"95":[[0,31,71],[1,237,9,100]],"96":[[0,329,43],[1,736,73,106]],"97":[[0,34,891],[1,982,134,105]],"98":[[0,148,583],[0,62,590],[1,148,583,98]],"99":[[0,845,825],[1,982,1000,94]],"100":[[0,50,566],[1,990,638,101]],"101":[[0,466,993],[1,19,72,99]],"102":[[0,72,46],[1,984,1000,92]],"103":[[0,106,957],[1,551,307,90],[1,996,275,91]],"104":[[0,21,892],[1,678,8,106],[1,828,1000,96]],"105":[[0,13,979],[1,997,111,103]],"106":[[0,985,557],[1,6,812,100]],"107":[[0,29,34],[1,972,998,102]],"108":[[0,265,1000],[1,967,684,32]],"109":[[0,54,987],[1,987,156,110]],"110":[[0,25,813],[1,2,414,112]],"111":[[0,46,119],[1,525,1000,108]],"112":[[0,37,415],[1,994,661,108]],"113":[[0,29,423],[1,993,154,114]],"114":[[0,812,1000],[1,103,8,112]],"115":[[0,56,914],[1,996,92,116]],"116":[[0,98,962],[1,5,973,115]],"117":[[0,61,974],[1,12,880,115],[1,231,375,13]],"121":[[0,92,940],[1,73,968,0]],"122":[[0,10,210],[1,993,904,123]],"123":[[0,25,533],[1,994,686,2]],"124":[[0,38,243],[1,983,668,127]],"125":[[0,74,882],[1,965,141,129]],"126":[[0,7,410],[1,995,342,122]],"127":[[0,50,161],[1,994,904,123]],"128":[[0,42,902],[1,992,96,126]],"129":[[0,15,228],[1,490,782,48]]};
        let tfs = {};
        const thumb = (l, t) => {
          const [w, h] = SZ[l] || [240, 160], r = (t && t.r) || 0, side = r % 180 !== 0, VW = side ? h : w, VH = side ? w : h, R = Math.max(w, h) * 0.06;
          const g = "translate(" + VW / 2 + " " + VH / 2 + ") rotate(" + r + ") scale(" + (t && t.m ? -1 : 1) + " " + (t && t.v ? -1 : 1) + ") translate(" + -w / 2 + " " + -h / 2 + ")";
          const mk = (EE[l] || []).map((m) => '<circle cx="' + m[1] * w / 1000 + '" cy="' + m[2] * h / 1000 + '" r="' + R + '" class="' + (m[0] ? "ex" : "en") + '" stroke-width="' + R * 0.35 + '"/>').join("");
          return '<span class="sg-img"><svg viewBox="0 0 ' + VW + " " + VH + '" preserveAspectRatio="xMidYMid meet"><g transform="' + g + '"><image href="maps/t/L' + l + '.webp" width="' + w + '" height="' + h + '" preserveAspectRatio="none"/>' + mk + "</g></svg><em>~" + (WALK[l] || "?") + " s to cross</em></span>";
        };
        function siegeView(sc) {
          siegeLoad();
          const wrap = document.createElement("div"); wrap.className = "sg";
          const top = document.createElement("div"); top.className = "sg-top"; wrap.appendChild(top);
          const hint = document.createElement("div"); hint.className = "sg-hint"; top.appendChild(hint);
          const chips = document.createElement("div"); chips.className = "sg-chips"; top.appendChild(chips);
          LOOK.concat([["All", null]]).forEach((g, i) => { const b = document.createElement("button"); b.type = "button"; b.dataset.look = i; b.textContent = g[0] + (g[1] ? " " + g[1].length : ""); chips.appendChild(b); });
          const strip = document.createElement("div"); strip.className = "sg-strip"; top.appendChild(strip);
          function fill() {
            chips.querySelectorAll("button").forEach((b) => b.classList.toggle("on", +b.dataset.look === look));
            const g = LOOK[look], ls = g ? g[1] : Object.keys(WALK).map(Number).sort((a, b) => (region(a) + NAMES[a]).localeCompare(region(b) + NAMES[b]));
            strip.innerHTML = ""; strip.scrollLeft = 0;
            ls.forEach((l) => { const c = document.createElement("button"); c.type = "button"; c.className = "sg-card"; c.dataset.pick = l; c.innerHTML = thumb(l) + "<b>" + NAMES[l] + "</b><i>" + region(l) + "</i>"; strip.appendChild(c); });
          }
          fill();
          strip.addEventListener("wheel", (e) => { if (!e.ctrlKey && Math.abs(e.deltaY) > Math.abs(e.deltaX)) { e.preventDefault(); strip.scrollLeft += e.deltaY; } }, { passive: false });
          const grid = document.createElement("div"); grid.className = "sg-grid"; wrap.appendChild(grid);
          const ctl = document.createElement("div"); ctl.className = "sg-ctl"; wrap.appendChild(ctl);
          ctl.innerHTML = '<span class="sg-cl"></span><button type="button" data-tf="l">⟲ Rotate left</button><button type="button" data-tf="r">⟳ Rotate right</button><button type="button" data-tf="m">⇋ Mirror</button><button type="button" data-tf="v">⇅ Flip</button><button type="button" data-tf="0">Reset</button><span class="sg-leg"><i class="en"></i>Way in <i class="ex"></i>Exit</span>';
          const msg = document.createElement("div"); msg.className = "sg-msg"; wrap.appendChild(msg);
          function draw() {
            grid.innerHTML = "";
            const used = {}; SLOTS.forEach((t) => { if (siege[t.k] != null) used[siege[t.k]] = t.n; });
            strip.querySelectorAll(".sg-card").forEach((c) => c.classList.toggle("used", !!used[c.dataset.pick]));
            grid.style.setProperty("--n", 5);
            const cur = SLOTS.find((t) => t.k === sel);
            ctl.querySelector(".sg-cl").textContent = cur ? "Selected " + cur.n.split(" ")[0] + (siege[sel] != null ? ": " + NAMES[siege[sel]] : " (empty)") : "";
            hint.innerHTML = cur && !cur.fixed ? "Picking for <b>" + cur.n + "</b>. Choose a group, then tap a screen to put it there." : "Tap a spot in the layout, then pick a screen for it.";
            SLOTS.forEach((t) => {
              const d = document.createElement("div"); d.className = "sg-slot" + (t.k === sel ? " on" : "") + (t.fixed ? " fixed" : "") + (t.k === "r1c3" ? " boss" : t.k === "r5c3" ? " home" : SPECIAL[t.k] ? " spec" : "");
              d.style.gridRow = t.r; d.style.gridColumn = t.c; d.dataset.slot = t.k;
              const l = siege[t.k];
              d.innerHTML = '<div class="sg-sn">' + t.n + (t.fixed ? " 🔒" : "") + "</div>" + (l != null ? thumb(l, tfs[t.k]) + "<b>" + NAMES[l] + "</b>" + (t.fixed ? "" : '<button type="button" class="sg-x" data-clear="' + t.k + '" aria-label="Clear">×</button>') + '<button type="button" class="sg-v" data-view="' + l + '">View</button>' : '<div class="sg-empty">+</div>');
              grid.appendChild(d);
            });
          }
          siegeRedraw = draw; draw();
          wrap.addEventListener("click", (e) => {
            const lk = e.target.closest("[data-look]"); if (lk) { e.preventDefault(); look = +lk.dataset.look; fill(); draw(); return; }
            const x = e.target.closest("[data-clear]"), v = e.target.closest("[data-view]"), pk = e.target.closest("[data-pick]"), sl = e.target.closest("[data-slot]");
            const tb = e.target.closest("[data-tf]");
            if (tb) { e.preventDefault(); e.stopPropagation(); if (siege[sel] == null) { msg.textContent = "Pick a block with a screen in it first."; return; }
              const t = Object.assign({ r: 0, m: 0, v: 0 }, tfs[sel]), a = tb.dataset.tf;
              if (a === "l") t.r = (t.r + 270) % 360; else if (a === "r") t.r = (t.r + 90) % 360; else if (a === "m") t.m = t.m ? 0 : 1; else if (a === "v") t.v = t.v ? 0 : 1; else { t.r = 0; t.m = 0; t.v = 0; }
              if (!t.r && !t.m && !t.v) delete tfs[sel]; else tfs[sel] = t; draw(); siegeSave(msg); return; }
            if (x) { e.preventDefault(); e.stopPropagation(); delete siege[x.dataset.clear]; delete tfs[x.dataset.clear]; sel = x.dataset.clear; draw(); siegeSave(msg); return; }
            if (v) { e.preventDefault(); e.stopPropagation(); pic(+v.dataset.view); return; }
            if (pk) { e.preventDefault(); e.stopPropagation(); const t = SLOTS.find((q) => q.k === sel); if (!t || t.fixed) { msg.textContent = "Tap a spot in the layout first."; return; }
              siege[sel] = +pk.dataset.pick; const nx = SLOTS.find((q) => !q.fixed && siege[q.k] == null); if (nx) sel = nx.k; draw(); siegeSave(msg); return; }
            if (sl) { e.preventDefault(); e.stopPropagation(); const t = SLOTS.find((q) => q.k === sl.dataset.slot); sel = t.k; draw(); return; }
          });
          sc.appendChild(wrap);
          const foot = document.createElement("div"); foot.className = "sm-foot";
          foot.textContent = "Siege layout: Helm's Deep is the start. Walk times are the long side of each screen at the hero's walking speed, so a winding path takes longer. Green circles are where you come into a screen, red circles are its exits (read by walking the hero onto every exit in the game). Rotate and mirror change the plan only. Picks save to your account. Nothing in the game changes yet; this is the plan the Siege map will be built from.";
          sc.appendChild(foot);
        }

        function bonusGrid(sc, small) {
          const cols = Math.max(...BONUS.map((m) => m.s.length));
          const g = document.createElement("div"); g.className = "sm-grid"; g.style.gridTemplateColumns = (small ? "78px" : "112px") + " repeat(" + cols + ", " + (small ? 96 : 120) + "px)"; g.style.gridTemplateRows = BONUS.map((m, i) => (i ? "18px " : "") + (small ? "100px" : "118px")).join(" "); sc.appendChild(g);
          BONUS.forEach((m, i) => {
            if (i) for (let c = 0; c <= cols; c++) { const d = document.createElement("div"); d.className = c ? "sm-empty" : "sm-gaphead"; g.appendChild(d); }
            const head = document.createElement("div"); head.className = "sm-hero"; head.textContent = m.name; g.appendChild(head);
            for (let c = 0; c < cols; c++) {
              const d = document.createElement("div"), v = m.s[c];
              if (!v) { d.className = "sm-empty"; g.appendChild(d); continue; }
              const l = v[0];
              d.className = "sm-b " + (v[1] ? "boss" : "n");
              d.innerHTML = "<b>" + NAMES[l] + "</b>" + (v[1] ? "<i class=\"sm-big\">" + v[1] + "</i><i>" + v[2] + "</i>" : "") + cnt(l);
              d.title = NAMES[l] + " (level " + l + ")"; d.dataset.l = l; g.appendChild(d);
            }
          });
          const foot = document.createElement("div"); foot.className = "sm-foot";
          foot.textContent = "Read from the game: each map's screens follow its exits, and big monsters are the enemies with the most hit points. The Nazgûl on Amon Sûl are from a picture of the map. Amon Sûl is one screen and Hornburg two.";
          sc.appendChild(foot);
        }
        function render() {
          const L = layout(), box = document.createElement("div"); box.id = "storyMap";
          const top = document.createElement("div"); top.className = "sm-top";
          const leg = tab === "story" ? '<span><b class="n"></b>Screen</span><span><b class="boss"></b>Big fight</span><span><b class="side"></b>Side quest</span><span><b class="team"></b>Team-up (both heroes walk it)</span><span><b class="n orc"></b>More Orc Heads</span>' : tab === "bonus" ? '<span><b class="n"></b>Screen</span><span><b class="boss"></b>Big monster</span>' : "";
          top.innerHTML = '<div class="sm-tabs"><button type="button" data-t="story"' + (tab === "story" ? ' class="on"' : "") + '>Story</button><button type="button" data-t="bonus"' + (tab === "bonus" ? ' class="on"' : "") + '>Bonus maps</button><button type="button" data-t="siege"' + (tab === "siege" ? ' class="on"' : "") + '>Siege</button></div><div class="sm-leg">' + leg + "</div>";
          top.querySelectorAll(".sm-tabs button").forEach((b) => b.addEventListener("click", (e) => { e.preventDefault(); if (tab === b.dataset.t) return; tab = b.dataset.t; const n = render(); el.replaceWith(n); el = n; }));
          const x = document.createElement("button"); x.type = "button"; x.className = "sm-close"; x.textContent = "Close"; x.addEventListener("click", (e) => { e.preventDefault(); close(); }); top.appendChild(x);
          box.appendChild(top);
          const sc = document.createElement("div"); sc.className = "sm-scroll"; box.appendChild(sc);
          pinch(sc);
          sc.addEventListener("click", (e) => { const b = e.target.closest(".sm-b[data-l]"); if (b) { e.preventDefault(); pic(+b.dataset.l); } });
          if (tab === "bonus") { bonusGrid(sc, window.innerHeight <= 500); return box; }
          if (tab === "siege") { siegeView(sc); return box; }
          const g = document.createElement("div"); g.className = "sm-grid"; const small = window.innerHeight <= 500; g.style.gridTemplateColumns = (small ? "78px" : "112px") + " repeat(" + L.cols + ", " + (small ? 72 : 92) + "px)"; sc.appendChild(g);
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
              if (BOSS[l] && BOSS[l] !== "Witch-king") t += "<i>" + BOSS[l] + "</i>";
              if (team) t += "<i>" + v.hs.map((h) => HEROES[h].name).join(" + ") + "</i>";
              if (o) t += '<u>Orc Heads ' + o + "</u>";
              t += cnt(l);
              d.innerHTML = t; d.title = NAMES[l] + " (" + rg + ", level " + l + ")"; d.dataset.l = l; g.appendChild(d);
            }
          }
          const foot = document.createElement("div"); foot.className = "sm-foot";
          foot.textContent = "Enemy counts are the monsters placed on each screen, sized by hit points (small under 40, medium under 150, large 150 and up). Spawners keep making more. Read from the game: where each mission starts, which screen each exit leads to, and the story scenes. Red marks are my reading of the story scenes; a few side screens the story never walks through are left out.";
          sc.appendChild(foot);
          return box;
        }
        // Pinch with two fingers (or Ctrl + mouse wheel / trackpad pinch on PC) to zoom the whole grid in and out (Jordan, 2026-11-10).
        let gz = 1;
        function pinch(sc) {
          const setZ = (z, fx, fy) => {
            z = Math.min(2.5, Math.max(0.25, z)); const kids = sc.children; if (!kids.length) return;
            const r = sc.getBoundingClientRect(), x = fx - r.left, y = fy - r.top, px = (sc.scrollLeft + x) / gz, py = (sc.scrollTop + y) / gz;
            gz = z; for (const k of kids) k.style.zoom = z;
            sc.scrollLeft = px * z - x; sc.scrollTop = py * z - y;
          };
          requestAnimationFrame(() => { for (const k of sc.children) k.style.zoom = gz; });
          let st = null;
          const dist = (t) => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
          sc.addEventListener("touchstart", (e) => { if (e.touches.length === 2) { st = { d: dist(e.touches), z: gz }; e.preventDefault(); } }, { passive: false });
          sc.addEventListener("touchmove", (e) => { if (st && e.touches.length === 2) { e.preventDefault(); const t = e.touches; setZ(st.z * dist(t) / st.d, (t[0].clientX + t[1].clientX) / 2, (t[0].clientY + t[1].clientY) / 2); } }, { passive: false });
          sc.addEventListener("touchend", (e) => { if (e.touches.length < 2) st = null; });
          // iPhone Safari sends its own gesture events for a pinch; stop the page zooming.
          ["gesturestart", "gesturechange"].forEach((n) => sc.addEventListener(n, (e) => e.preventDefault()));
          sc.addEventListener("wheel", (e) => { if (e.ctrlKey) { e.preventDefault(); setZ(gz * Math.exp(-e.deltaY / 200), e.clientX, e.clientY); } }, { passive: false });
        }
        // Tap or click a block: overhead picture of the screen with no monsters (captured from the game, tools/storymap/cap.py).
        let pv = null, zoom = 0;
        function pic(l) {
          closePic(); zoom = 0;
          const v = document.createElement("div"); v.id = "smPic";
          const bar = document.createElement("div"); bar.className = "smp-bar";
          const rg = region(l); bar.innerHTML = "<b>" + NAMES[l] + "</b><span>" + (rg ? rg + " · " : "") + "level " + l + "</span>";
          const z = document.createElement("button"); z.type = "button"; z.textContent = "Zoom in"; bar.appendChild(z);
          const x = document.createElement("button"); x.type = "button"; x.textContent = "Back"; x.addEventListener("click", (e) => { e.preventDefault(); closePic(); }); bar.appendChild(x);
          const wrap = document.createElement("div"); wrap.className = "smp-wrap";
          const img = new Image(); img.alt = NAMES[l] + " from above"; img.decoding = "async";
          const msg = document.createElement("div"); msg.className = "smp-msg"; msg.textContent = "Loading picture…"; wrap.appendChild(msg);
          const fit = () => { if (!img.naturalWidth) return; const W = wrap.clientWidth - 16, H = wrap.clientHeight - 16, f = Math.min(W / img.naturalWidth, H / img.naturalHeight); const k = zoom ? Math.max(1, f) * (zoom === 1 ? 2 : 4) : Math.min(f, 3); img.style.width = Math.round(img.naturalWidth * k) + "px"; wrap.classList.toggle("zoomed", !!zoom); z.textContent = zoom === 2 ? "Fit" : "Zoom in"; };
          img.onload = () => { msg.remove(); wrap.appendChild(img); fit(); };
          img.onerror = () => { msg.textContent = "No picture for this screen yet."; };
          img.src = "maps/L" + l + ".webp";
          z.addEventListener("click", (e) => { e.preventDefault(); const cx = (wrap.scrollLeft + wrap.clientWidth / 2) / (wrap.scrollWidth || 1), cy = (wrap.scrollTop + wrap.clientHeight / 2) / (wrap.scrollHeight || 1); zoom = (zoom + 1) % 3; fit(); wrap.scrollLeft = cx * wrap.scrollWidth - wrap.clientWidth / 2; wrap.scrollTop = cy * wrap.scrollHeight - wrap.clientHeight / 2; });
          // Drag to look around with a mouse (fingers scroll natively).
          let dr = null;
          wrap.addEventListener("pointerdown", (e) => { if (e.pointerType !== "mouse") return; dr = { x: e.clientX, y: e.clientY, l: wrap.scrollLeft, t: wrap.scrollTop }; wrap.setPointerCapture(e.pointerId); e.preventDefault(); });
          wrap.addEventListener("pointermove", (e) => { if (dr) { wrap.scrollLeft = dr.l - (e.clientX - dr.x); wrap.scrollTop = dr.t - (e.clientY - dr.y); } });
          wrap.addEventListener("pointerup", () => { dr = null; });
          v.appendChild(bar); v.appendChild(wrap); el.appendChild(v); pv = v;
          v._fit = fit; window.addEventListener("resize", fit);
        }
        function closePic() { if (pv) { window.removeEventListener("resize", pv._fit); pv.remove(); pv = null; } }
        function open() { if (el) return; el = render(); document.body.appendChild(el); }
        function close() { closePic(); if (el) { el.remove(); el = null; } }
        return { open, close, layout, isOpen: () => !!el, picOpen: () => !!pv, closePic };
      })();
