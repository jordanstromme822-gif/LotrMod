# Play Room v248: the 3D World shows the Isengard region (v247) as the one piece it now is in the game: Campsite,
# Flooded Field and Tower Base on one slab, with the ground between and Orthanc's horns, instead of three screens
# joined by bridges. The region picture (maps/x/R51.webp, tools/region/w3d.py) is placed from where the Flooded Field
# screen sits, so moves saved in the 3D World still place it. Taps on it still pick the screen underneath.
# Usage: python3 world3d-v248.py index.html|world3d.js
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (old[:70], s.count(old))
    s = s.replace(old, new)

# the region table, and the region's screens placed where they are in the game's region (moves of any of them move
# the whole region, as the screen it is placed from)
rep("""  function shifted(L0) {   // the layout with the player's moves applied (copies; World3D.layout stays as the game uses it)
    const T = {}; Object.keys(L0.T).forEach((k) => { const t = Object.assign({}, L0.T[k]), o = OFF[k]; if (o) { t.x += o[0]; t.y += o[1]; } T[k] = t; });
    const mv = (l, p) => { const o = OFF[l]; return o && p ? [p[0] + o[0], p[1] + o[1]] : p; };""",
"""  // v248 regions (tools/region): screens the game now joins into one level. `of` = each screen's top-left in the region
  // (px); the region is placed from screen `at` and drawn from its own picture.
  const W3R = [{ at: 51, src: "maps/x/R51.webp", w: 7392, h: 16000, of: { 50: [4032, 4480], 51: [3520, 13056], 55: [5376, 10208] } }];
  const regOf = (l) => W3R.find((r) => r.of[l]);
  const offOf = (L0, l) => {   // the move of screen l, with region screens kept where they are in their region
    const r = regOf(l); if (!r || !L0.T[r.at] || !L0.T[l]) return OFF[l];
    const oa = OFF[r.at] || [0, 0], a = L0.T[r.at], t = L0.T[l];
    return [a.x + oa[0] + r.of[l][0] - r.of[r.at][0] - t.x, a.y + oa[1] + r.of[l][1] - r.of[r.at][1] - t.y];
  };
  function shifted(L0) {   // the layout with the player's moves applied (copies; World3D.layout stays as the game uses it)
    const T = {}; Object.keys(L0.T).forEach((k) => { const t = Object.assign({}, L0.T[k]), o = offOf(L0, +k); if (o) { t.x += o[0]; t.y += o[1]; } T[k] = t; });
    const mv = (l, p) => { const o = offOf(L0, l); return o && p ? [p[0] + o[0], p[1] + o[1]] : p; };""")
rep("""      const o = OFF[g.l] || [0, 0]; OFF[g.l] = [o[0] + dx, o[1] + dy]; if (!OFF[g.l][0] && !OFF[g.l][1]) delete OFF[g.l];""",
    """      const gl = regOf(g.l) ? regOf(g.l).at : g.l;
      const o = OFF[gl] || [0, 0]; OFF[gl] = [o[0] + dx, o[1] + dy]; if (!OFF[gl][0] && !OFF[gl][1]) delete OFF[gl];""")
rep("""    let loaded = 0;
    const thumbQ = Object.keys(tiles).map(Number);""",
"""    // v248 regions: one slab with the region's own picture over the screens it is made of (placed from screen `at`). The screens' own slabs are hidden but still pick taps.
    const sameRegion = (a, b) => !!regOf(a) && regOf(a) === regOf(b);
    const regionMeshes = [];
    W3R.forEach((r) => {
      const a = tiles[r.at]; if (!a) return;
      const x = a.t.x - r.of[r.at][0], y = a.t.y - r.of[r.at][1], w = r.w / U, d = r.h / U, hgt = top(r.at) + 0.6;
      const mat = new THREE.MeshBasicMaterial({ color: 0x555555 });
      const geo = new THREE.BoxGeometry(w, hgt, d), m = new THREE.Mesh(geo, [side, side, mat, bottom, side, side]);
      m.position.set(x / U + w / 2, hgt / 2 - 0.6 + 0.01, y / U + d / 2); scene.add(m);
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0xc79a3e, transparent: true, opacity: 0.85 }));
      edges.position.copy(m.position); scene.add(edges);
      Object.keys(r.of).forEach((l) => { const k = tiles[l]; if (k) { k.m.visible = false; k.edges.visible = false; k.regionOf = r; } });
      regionMeshes.push({ r, m, mat, edges });
      loader.load(r.src, (tx) => { if (view.dead) { tx.dispose(); return; } tx.anisotropy = maxAniso; mat.map = tx; mat.color.set(0xffffff); mat.needsUpdate = true; dirty(); }, undefined, () => {});
    });
    let loaded = 0;
    const thumbQ = Object.keys(tiles).map(Number);""")
rep("""      if (!k.real) return; const key = pairKey(k.a, k.b); if (bridged[key]) return;""",
    """      if (!k.real) return; const key = pairKey(k.a, k.b); if (bridged[key] || sameRegion(k.a, k.b)) return;""")
rep("""      bridges.forEach((br) => { br.tx && br.tx.dispose(); br.mat && br.mat.dispose(); });""",
    """      bridges.forEach((br) => { br.tx && br.tx.dispose(); br.mat && br.mat.dispose(); });
      regionMeshes.forEach((q) => { q.mat.map && q.mat.map.dispose(); q.mat.dispose(); q.m.geometry.dispose(); });""")
rep("""view.api = { pickHero, showCard, fitTo, cam, goal, tiles, layout: L, dirty, bridges,""",
    """view.api = { pickHero, showCard, fitTo, cam, goal, tiles, layout: L, dirty, bridges, regions: regionMeshes,""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
