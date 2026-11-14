import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import http from 'node:http';
import {createApp} from '../http.mjs';

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
