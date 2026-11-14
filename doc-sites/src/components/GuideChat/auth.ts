export type AuthConfig = {clientId: string; domain: string; redirectUri: string; userPoolId: string};
const TOKEN_KEY = 'skills-guide-access';
const FLOW_KEY = 'skills-guide-pkce';
const b64 = (bytes: Uint8Array) => btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

export function accessToken(): string | null {
  try {
    const saved = JSON.parse(sessionStorage.getItem(TOKEN_KEY) || 'null');
    if (saved?.expires > Date.now()) return saved.token;
    sessionStorage.removeItem(TOKEN_KEY);
  } catch { /* Unavailable storage means sign-in is required. */ }
  return null;
}

export async function signIn(config: AuthConfig) {
  const verifier = b64(crypto.getRandomValues(new Uint8Array(32)));
  const state = b64(crypto.getRandomValues(new Uint8Array(32)));
  const challenge = b64(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))));
  sessionStorage.setItem(FLOW_KEY, JSON.stringify({verifier, state, created: Date.now(), returnPath: location.pathname + location.search + location.hash}));
  const url = new URL('/oauth2/authorize', config.domain);
  url.search = new URLSearchParams({client_id: config.clientId, response_type: 'code', scope: 'openid',
    redirect_uri: config.redirectUri, state, code_challenge: challenge, code_challenge_method: 'S256'}).toString();
  location.assign(url);
}

let completion: Promise<boolean> | undefined;
export function completeSignIn(config: AuthConfig): Promise<boolean> {
  if (completion) return completion;
  const url = new URL(location.href);
  if (!url.searchParams.has('code') && !url.searchParams.has('error')) return Promise.resolve(false);
  completion = (async () => {
    const code = url.searchParams.get('code');
    const state = url.searchParams.get('state');
    const saved = JSON.parse(sessionStorage.getItem(FLOW_KEY) || 'null');
    sessionStorage.removeItem(FLOW_KEY);
    for (const key of ['code', 'state', 'error', 'error_description']) url.searchParams.delete(key);
    history.replaceState(null, '', url.pathname + url.search);
    if (!code || !saved || saved.state !== state || Date.now() - saved.created > 600000) throw new Error('sign_in_failed');
    const response = await fetch(new URL('/oauth2/token', config.domain), {
      method: 'POST', headers: {'content-type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({grant_type: 'authorization_code', client_id: config.clientId,
        code, redirect_uri: config.redirectUri, code_verifier: saved.verifier}),
    });
    const tokens = await response.json();
    if (!response.ok || typeof tokens.access_token !== 'string' || !Number.isFinite(tokens.expires_in)) throw new Error('sign_in_failed');
    // Store only the short-lived access token in this tab. Discard refresh and ID tokens.
    sessionStorage.setItem(TOKEN_KEY, JSON.stringify({token: tokens.access_token, expires: Date.now() + tokens.expires_in * 1000 - 10000}));
    const destination = new URL(saved.returnPath || '/', config.redirectUri);
    const sameOrigin = destination.origin === new URL(config.redirectUri).origin;
    sessionStorage.setItem('skills-guide-open', '1');
    // Each Docusaurus locale has a distinct application bundle. History changes
    // alone leave the callback's Korean application running under an English URL.
    location.replace(sameOrigin ? destination.pathname + destination.search + destination.hash : '/');
    return true;
  })();
  return completion;
}

export function signOut(config: AuthConfig | null) {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(FLOW_KEY);
  if (config) {
    const url = new URL('/logout', config.domain);
    url.search = new URLSearchParams({client_id: config.clientId, logout_uri: config.redirectUri}).toString();
    location.assign(url);
  }
}
