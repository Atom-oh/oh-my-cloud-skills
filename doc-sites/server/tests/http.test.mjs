import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
import {createApp} from '../http.mjs';
import {MAX_CHAT_BODY_BYTES, validateQuestion} from '../chat.mjs';

test('oversized delayed bodies drain before the next request on the connection', async (t) => {
  let calls = 0;
  const app = createApp({
    buildDir: tmpdir(), origin: 'https://skills.example.com', publicConfig: {},
    authenticate: async () => 'subject', consumeQuota: async () => true,
    answer: async () => { calls++; return {answer: 'unused'}; },
  });
  await new Promise((resolve) => app.listen(0, '127.0.0.1', resolve));
  const socket = net.connect(app.address().port, '127.0.0.1');
  t.after(async () => { socket.destroy(); await new Promise((resolve) => app.close(resolve)); });
  const first = Buffer.alloc(MAX_CHAT_BODY_BYTES + 8192, 'x');
  const remainder = Buffer.alloc(1024 * 1024, 'x');
  const headers = [
    'POST /api/chat HTTP/1.1', 'Host: localhost',
    'Content-Type: application/json', 'Origin: https://skills.example.com',
    'Authorization: Bearer valid', `Content-Length: ${first.length + remainder.length}`,
    'Connection: keep-alive', '', '',
  ].join('\r\n');
  const next = 'GET /api/health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n';
  const response = await new Promise((resolve, reject) => {
    let text = '', sentRemainder = false;
    const timer = setTimeout(() => {
      socket.destroy(); reject(new Error('Delayed body prevented connection reuse'));
    }, 3000);
    socket.once('error', (error) => { clearTimeout(timer); reject(error); });
    socket.on('data', (chunk) => {
      text += chunk.toString();
      if (!sentRemainder && text.includes('HTTP/1.1 400')) {
        sentRemainder = true;
        setTimeout(() => socket.write(Buffer.concat([remainder, Buffer.from(next)])), 25);
      }
      if (text.includes('HTTP/1.1 200')) { clearTimeout(timer); resolve(text); }
    });
    socket.once('connect', () => socket.write(Buffer.concat([Buffer.from(headers), first])));
  });
  assert.deepEqual([...response.matchAll(/HTTP\/1\.1 (\d{3})/g)].map((m) => m[1]), ['400', '200']);
  assert.equal(calls, 0);
});

test('HTTP accepts the full multilingual history contract and bounds oversized bodies', async (t) => {
  const received = [];
  const app = createApp({
    buildDir: tmpdir(), origin: 'https://skills.example.com', publicConfig: {},
    authenticate: async () => 'subject', consumeQuota: async () => true,
    answer: async (question) => { received.push(question); return {answer: 'ok', sources: []}; },
  });
  await new Promise((r) => app.listen(0, '127.0.0.1', r));
  t.after(() => new Promise((r) => app.close(r)));
  const payload = {message: '가'.repeat(2000), locale: 'ko',
    history: Array.from({length: 8}, (_, i) => ({role: i % 2 ? 'assistant' : 'user', content: '한'.repeat(2000)}))};
  const expected = validateQuestion(payload);
  const post = (body) => fetch(`http://127.0.0.1:${app.address().port}/api/chat`, {
    method: 'POST', headers: {'content-type': 'application/json', authorization: 'Bearer valid', origin: 'https://skills.example.com'},
    body,
  });
  const encoded = JSON.stringify(payload);
  assert.equal((await post(encoded)).status, 200);
  const escaped = encoded.replace(/[^\x00-\x7f]/g, (char) => `\\u${char.charCodeAt(0).toString(16).padStart(4, '0')}`);
  assert.equal((await post(escaped)).status, 200);
  assert.deepEqual(received, [expected, expected]);
  assert.equal((await post(JSON.stringify({message: 'x'.repeat(200_000)}))).status, 400);
  assert.equal(received.length, 2);
});

test('HTTP boundary serves guides, preserves redirects and protects chat', async (t) => {
  const root = await mkdtemp(path.join(tmpdir(), 'skills-http-'));
  await mkdir(path.join(root, 'en/docs/intro'), {recursive: true});
  await writeFile(path.join(root, 'index.html'), '<h1>Guide</h1>');
  await writeFile(path.join(root, 'en/docs/intro/index.html'), '<h1>English</h1>');
  await writeFile(path.join(root, '404.html'), 'Not found');
  let calls = 0;
  const app = createApp({
    buildDir: root, origin: 'https://skills.example.com',
    publicConfig: {auth: {clientId: 'public'}},
    authenticate: async (token) => { if (token !== 'valid') throw new Error('bad token'); return 'subject'; },
    consumeQuota: async () => true,
    answer: async () => { calls++; return {answer: 'Grounded answer', sources: []}; },
  });
  await new Promise((resolve) => app.listen(0, '127.0.0.1', resolve));
  t.after(async () => { await new Promise((r) => app.close(r)); await rm(root, {recursive: true}); });
  const base = `http://127.0.0.1:${app.address().port}`;
  assert.equal((await fetch(base)).status, 200);
  assert.match(await (await fetch(`${base}/en/docs/intro`)).text(), /English/);
  const old = await fetch(`${base}/oh-my-cloud-skills/en/docs/intro?q=notes`, {redirect: 'manual'});
  assert.equal(old.status, 308);
  assert.equal(old.headers.get('location'), '/en/docs/intro?q=notes');
  assert.equal((await fetch(`${base}/missing`)).status, 404);
  const config = await fetch(`${base}/api/config`);
  assert.equal(config.headers.get('cache-control'), 'no-store');
  const post = (body, token = '', origin = 'https://skills.example.com') => fetch(`${base}/api/chat`, {
    method: 'POST', headers: {'content-type': 'application/json', origin, authorization: `Bearer ${token}`},
    body: JSON.stringify(body),
  });
  assert.equal((await post({message: 'test'})).status, 401);
  assert.equal((await post({message: 'test'}, 'valid', 'https://attacker.example')).status, 403);
  assert.equal((await post({message: 'x'.repeat(2001)}, 'valid')).status, 400);
  assert.equal((await post({message: 'test'}, 'valid')).status, 200);
  assert.equal(calls, 1);
  const raw = (url) => new Promise((resolve) => {
    http.get(`${base}${url}`, (res) => { res.resume(); resolve(res.statusCode); });
  });
  assert.equal(await raw('/%252e%252e/server/package.json'), 400);
  assert.equal(await raw('/%2e%2e%2fserver/package.json'), 400);
  assert.equal(await raw('/oh-my-cloud-skills/%0a'), 400);
  const external = await fetch(`${base}/oh-my-cloud-skills//attacker.example/`, {redirect: 'manual'});
  assert.equal(external.status, 400);
  const korean = await fetch(`${base}/oh-my-cloud-skills/${encodeURIComponent('가이드')}?q=notes`, {redirect: 'manual'});
  assert.equal(korean.status, 308);
  assert.equal(korean.headers.get('location'), `/${encodeURIComponent('가이드')}?q=notes`);
});

test('quota and provider failures return safe errors with no chat text', async (t) => {
  let quota = false;
  const app = createApp({
    buildDir: tmpdir(), origin: 'https://skills.example.com', publicConfig: {},
    authenticate: async () => 'subject', consumeQuota: async () => quota,
    answer: async () => { throw new Error('secret provider details'); },
  });
  await new Promise((r) => app.listen(0, '127.0.0.1', r));
  t.after(() => new Promise((r) => app.close(r)));
  const post = () => fetch(`http://127.0.0.1:${app.address().port}/api/chat`, {
    method: 'POST', headers: {'content-type': 'application/json', authorization: 'Bearer valid', origin: 'https://skills.example.com'},
    body: JSON.stringify({message: 'test'}),
  });
  assert.equal((await post()).status, 429);
  quota = true;
  const response = await post();
  assert.equal(response.status, 503);
  assert.doesNotMatch(await response.text(), /secret/);
});
