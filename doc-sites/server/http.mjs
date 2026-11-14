import http from 'node:http';
import {readFile, realpath, stat} from 'node:fs/promises';
import path from 'node:path';
import {MAX_CHAT_BODY_BYTES, validateQuestion} from './chat.mjs';

const MIME = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml', '.pdf': 'application/pdf'};
function json(res, status, value) {
  res.writeHead(status, {'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store'});
  res.end(JSON.stringify(value));
}

async function body(req) {
  const chunks = []; let size = 0;
  try {
    for await (const chunk of req.iterator({destroyOnReturn: false})) {
      size += chunk.length;
      if (size > MAX_CHAT_BODY_BYTES) throw new Error('Invalid request body');
      chunks.push(chunk);
    }
  } catch (error) {
    // Iterator cleanup can pause the request; drain only after that boundary.
    req.resume();
    throw error;
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

export function createApp({buildDir, origin, publicConfig, authenticate, consumeQuota, answer}) {
  const root = path.resolve(buildDir);
  const handle = async (req, res) => {
    res.setHeader('x-content-type-options', 'nosniff');
    res.setHeader('referrer-policy', 'strict-origin-when-cross-origin');
    res.setHeader('permissions-policy', 'camera=(), microphone=(), geolocation=()');
    res.setHeader('x-frame-options', 'SAMEORIGIN');
    let pathname, query;
    try {
      const [rawPath, ...rest] = (req.url || '/').split('?');
      pathname = decodeURIComponent(rawPath);
      query = rest.length ? `?${rest.join('?')}` : '';
      // Reject second decoding, dot-segments and backslashes before normalizing.
      if (/%[0-9a-f]{2}/i.test(pathname) || /[\\\u0000-\u001f\u007f]/.test(pathname)
        || pathname.split('/').some((s) => s === '..' || s === '.')) throw new Error();
    } catch { return json(res, 400, {error: 'invalid_path'}); }
    if (pathname === '/api/config' && req.method === 'GET') return json(res, 200, publicConfig);
    if (pathname === '/api/health' && req.method === 'GET') return json(res, 200, {ok: true});
    if (pathname === '/api/chat') {
      if (req.method !== 'POST') return json(res, 405, {error: 'method_not_allowed'});
      if (req.headers.origin !== origin) return json(res, 403, {error: 'origin_not_allowed'});
      if (!req.headers['content-type']?.startsWith('application/json')) return json(res, 415, {error: 'json_required'});
      const token = req.headers.authorization?.match(/^Bearer ([^\s]+)$/)?.[1];
      if (!token) return json(res, 401, {error: 'sign_in_required'});
      let subject;
      try { subject = await authenticate(token); } catch { return json(res, 401, {error: 'sign_in_required'}); }
      let question;
      try { question = validateQuestion(await body(req)); } catch { return json(res, 400, {error: 'invalid_question'}); }
      const abort = new AbortController();
      const timer = setTimeout(() => abort.abort(), 55000);
      res.on('close', () => { if (!res.writableEnded) abort.abort(); });
      try {
        if (!await consumeQuota(subject, abort.signal)) {
          res.setHeader('retry-after', '3600');
          return json(res, 429, {error: 'daily_limit'});
        }
        const response = await answer(question, abort.signal);
        if (!res.destroyed) json(res, 200, response);
      } catch {
        // Neither user text, JWTs nor provider exception details enter logs.
        if (!res.destroyed) json(res, 503, {error: 'temporarily_unavailable'});
      } finally { clearTimeout(timer); }
      return;
    }
    if (pathname.startsWith('/api/')) return json(res, 404, {error: 'not_found'});
    if (!['GET', 'HEAD'].includes(req.method)) return json(res, 405, {error: 'method_not_allowed'});
    if (pathname === '/oh-my-cloud-skills' || pathname.startsWith('/oh-my-cloud-skills/')) {
      const destination = pathname.slice('/oh-my-cloud-skills'.length) || '/';
      if (destination.startsWith('//')) return json(res, 400, {error: 'invalid_path'});
      const encoded = destination.split('/').map(encodeURIComponent).join('/');
      res.writeHead(308, {location: encoded + query});
      return res.end();
    }
    try {
      let file = path.resolve(root, `.${pathname}`);
      if (!file.startsWith(root + path.sep) && file !== root) return json(res, 400, {error: 'invalid_path'});
      let info;
      try { info = await stat(file); } catch {
        if (!path.extname(file)) { file += '.html'; info = await stat(file); }
        else throw new Error();
      }
      if (info.isDirectory()) file = path.join(file, 'index.html');
      const resolved = await realpath(file);
      if (!resolved.startsWith(root + path.sep)) return json(res, 400, {error: 'invalid_path'});
      const data = await readFile(resolved);
      const extension = path.extname(file);
      res.writeHead(200, {'content-type': MIME[extension] || 'application/octet-stream',
        'cache-control': extension === '.html' ? 'public, max-age=0, must-revalidate' : 'public, max-age=3600'});
      res.end(req.method === 'HEAD' ? undefined : data);
    } catch {
      let page;
      try { page = await readFile(path.join(root, '404.html')); } catch { page = 'Not found'; }
      res.writeHead(404, {'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store'});
      res.end(req.method === 'HEAD' ? undefined : page);
    }
  };
  const server = http.createServer((req, res) => {
    handle(req, res).catch(() => {
      if (!res.headersSent && !res.destroyed) json(res, 500, {error: 'request_failed'});
      else if (!res.destroyed) res.destroy();
    });
  });
  server.requestTimeout = 65000;
  server.headersTimeout = 10000;
  return server;
}
