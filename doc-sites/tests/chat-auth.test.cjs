const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');
const ts = require('typescript');

function browser(href) {
  const values = new Map();
  let navigation;
  const location = new URL(href);
  location.replace = (url) => {navigation = url;};
  location.assign = (url) => {navigation = String(url);};
  const sandbox = {
    exports: {}, URL, URLSearchParams, Uint8Array, TextEncoder, Date, JSON,
    crypto: webcrypto, btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
    location, history: {replaceState() {}},
    sessionStorage: {getItem: (k) => values.get(k) || null, setItem: (k, v) => values.set(k, v), removeItem: (k) => values.delete(k)},
    fetch: async () => ({ok: true, json: async () => ({access_token: 'test-access-token', expires_in: 300})}),
    window: {dispatchEvent() {}}, PopStateEvent: class {},
  };
  const source = fs.readFileSync(path.resolve(__dirname, '../src/components/GuideChat/auth.ts'), 'utf8');
  const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}}).outputText;
  vm.runInNewContext(compiled, sandbox);
  return {api: sandbox.exports, values, navigation: () => navigation};
}
const config = {clientId: 'public-client', domain: 'https://login.example.com', redirectUri: 'https://skills.example.com/'};

test('English callback reloads the correct locale application including its fragment', async () => {
  const b = browser('https://skills.example.com/?code=test-code&state=test-state');
  b.values.set('skills-guide-pkce', JSON.stringify({verifier: 'test-verifier', state: 'test-state',
    created: Date.now(), returnPath: '/en/docs/co-agent/overview?source=guide#ready'}));
  assert.equal(await b.api.completeSignIn(config), true);
  assert.equal(b.navigation(), '/en/docs/co-agent/overview?source=guide#ready');
  assert.equal(b.values.has('skills-guide-pkce'), false);
  assert.equal(JSON.parse(b.values.get('skills-guide-access')).token, 'test-access-token');
});
test('sign-in saves the current fragment and rejects mismatched state', async () => {
  const b = browser('https://skills.example.com/en/docs/co-agent/overview#ready');
  await b.api.signIn(config);
  assert.equal(JSON.parse(b.values.get('skills-guide-pkce')).returnPath, '/en/docs/co-agent/overview#ready');
  const invalid = browser('https://skills.example.com/?code=test-code&state=wrong');
  invalid.values.set('skills-guide-pkce', JSON.stringify({state: 'expected', created: Date.now()}));
  await assert.rejects(invalid.api.completeSignIn(config), /sign_in_failed/);
  assert.equal(invalid.values.has('skills-guide-access'), false);
});
