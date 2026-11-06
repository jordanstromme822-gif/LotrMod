// Small static file server for local play: `npm start`, then open http://localhost:8080
// Later steps add the online lobby to this same server.
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), 'client');
const port = Number(process.env.PORT) || 8080;
const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

http
  .createServer(async (req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const file = normalize(join(root, urlPath.endsWith('/') ? urlPath + 'index.html' : urlPath));
    if (!file.startsWith(root)) {
      res.writeHead(403).end();
      return;
    }
    try {
      const body = await readFile(file);
      res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream', 'cache-control': 'no-cache' });
      res.end(body);
    } catch {
      res.writeHead(404).end('Not found');
    }
  })
  .listen(port, () => console.log(`Game running at http://localhost:${port}`));
