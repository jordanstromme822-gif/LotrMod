// node prof.js profile.json -> self time by function (top 40) and by url
const p = JSON.parse(require('fs').readFileSync(process.argv[2])); const byId = new Map(p.nodes.map(n => [n.id, n]));
const self = new Map(); const dt = p.timeDeltas; let tot = 0;
p.samples.forEach((id, i) => { const n = byId.get(id); const d = dt[i] || 0; tot += d; const cf = n.callFrame; const k = (cf.functionName || '(anon)') + ' ' + (cf.url||'').split('/').pop().slice(0,30) + ':' + cf.lineNumber; self.set(k, (self.get(k) || 0) + d); });
const top = [...self].sort((a, b) => b[1] - a[1]).slice(0, +(process.argv[3]||45));
for (const [k, v] of top) console.log((100 * v / tot).toFixed(1).padStart(5) + '%  ' + k);
const g = new Map(); p.samples.forEach((id, i) => { const n = byId.get(id); const cf = n.callFrame; const k = cf.url.includes('site.test/') && !cf.url.includes('.wasm') ? (cf.url.endsWith('.js') ? 'js:' + cf.url.split('/').pop() : 'page') : /wasm/.test(cf.functionName) ? 'wasm' : cf.functionName; g.set(k, (g.get(k) || 0) + (dt[i] || 0)); });
console.log('--- groups'); for (const [k, v] of [...g].sort((a, b) => b[1] - a[1]).slice(0, 15)) console.log((100 * v / tot).toFixed(1).padStart(5) + '%  ' + k);
