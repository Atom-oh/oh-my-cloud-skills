import React, {useEffect, useRef, useState} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {translate} from '@docusaurus/Translate';
import {useLocation} from '@docusaurus/router';
import {guides} from '../GuideWorkspace/guides';
import Icon from '../GuideWorkspace/Icon';
import {accessToken, completeSignIn, signIn, signOut, type AuthConfig} from './auth';
import styles from './styles.module.css';

type Message = {role: 'user' | 'assistant'; content: string; sources?: {title: string; url: string}[]; degraded?: boolean};
export default function GuideChat() {
  const location = useLocation();
  const {i18n} = useDocusaurusContext();
  const [open, setOpen] = useState(false);
  const [plugin, setPlugin] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [auth, setAuth] = useState<AuthConfig | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [error, setError] = useState('');
  const input = useRef<HTMLTextAreaElement>(null);
  const launch = useRef<HTMLButtonElement>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    let active = true;
    fetch('/api/config').then((r) => { if (!r.ok) throw new Error(); return r.json(); }).then(async (config) => {
      if (!active) return;
      setAvailable(config.chatAvailable === true); setAuth(config.auth);
      if (config.auth) {
        try {
          const completed = await completeSignIn(config.auth);
          if (active) {
            setSignedIn(Boolean(accessToken()));
            if (completed) setOpen(true);
            else {
              const reopen = sessionStorage.getItem('skills-guide-open') === '1';
              sessionStorage.removeItem('skills-guide-open');
              if (reopen) setOpen(true);
            }
          }
        } catch {
          if (active) { setSignedIn(false); setOpen(true); setError('sign_in_failed'); }
        }
      }
    }).catch(() => { if (active) { setAvailable(false); setError('configuration'); } });
    const show = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (guides.some((g) => g.id === detail.plugin)) {
        controller.current?.abort(); controller.current = null; setBusy(false); setPlugin(detail.plugin); setMessages([]);
      }
      setQuestion(detail.question || ''); setOpen(true); setError('');
    };
    const context = (event: Event) => {
      const id = (event as CustomEvent).detail;
      if (guides.some((g) => g.id === id)) changePlugin(id);
    };
    window.addEventListener('guide-chat', show);
    window.addEventListener('guide-context', context);
    return () => {
      active = false; window.removeEventListener('guide-chat', show);
      window.removeEventListener('guide-context', context); controller.current?.abort();
    };
  }, []);
  useEffect(() => {
    const query = new URLSearchParams(location.search).get('plugin');
    const section = location.pathname.match(/\/docs\/([^/]+)/)?.[1];
    const id = query || (section === 'remarp-guide' ? 'aws-content-plugin' : section);
    if (id && guides.some((g) => g.id === id)) changePlugin(id);
  }, [location.pathname, location.search]);
  useEffect(() => { if (open) input.current?.focus(); }, [open]);
  function close() { setOpen(false); launch.current?.focus(); }
  function changePlugin(id: string) {
    controller.current?.abort(); controller.current = null; setBusy(false); setPlugin(id); setMessages([]); setError('');
  }
  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!question.trim() || busy) return;
    const token = accessToken();
    if (!token) { setSignedIn(false); setError('sign_in_required'); return; }
    const text = question.trim();
    const request = new AbortController(); controller.current = request;
    const history = messages.slice(-8).map(({role, content}) => ({role, content: content.slice(0, 2000)}));
    setMessages((previous) => [...previous, {role: 'user', content: text}]);
    setQuestion(''); setBusy(true); setError('');
    const timer = window.setTimeout(() => request.abort(), 60000);
    try {
      const response = await fetch('/api/chat', {method: 'POST',
        headers: {'content-type': 'application/json', authorization: `Bearer ${token}`},
        body: JSON.stringify({message: text, plugins: plugin ? [plugin] : [], locale: i18n.currentLocale, history}),
        signal: request.signal});
      const data = await response.json();
      if (!response.ok) { if (response.status === 401) setSignedIn(false); throw new Error(data.error || 'unavailable'); }
      if (typeof data.answer !== 'string') throw new Error('unavailable');
      if (controller.current === request) setMessages((previous) => [...previous, {role: 'assistant', content: data.answer,
        sources: Array.isArray(data.sources) ? data.sources.filter((s) => /^\/(?:en\/)?docs\/[\w/-]+$/.test(s.url) && typeof s.title === 'string') : [],
        degraded: data.degraded === true}]);
    } catch (failure) {
      if (controller.current === request) {
        setError(failure instanceof Error ? failure.message : 'unavailable');
        setQuestion(text);
        setMessages((previous) => previous.slice(0, -1));
      }
    } finally {
      window.clearTimeout(timer);
      if (controller.current === request) setBusy(false);
    }
  }
  const errorText = error === 'daily_limit'
    ? translate({id: 'chat.limit', message: 'The daily question limit has been reached. You can continue using the guides and try again tomorrow.'})
    : ['sign_in_required', 'sign_in_failed'].includes(error)
      ? translate({id: 'chat.expired', message: 'Please sign in again to continue.'})
      : translate({id: 'chat.error', message: 'The guide assistant is unavailable right now. Your question is kept here so you can retry.'});
  return (
    <>
      <button ref={launch} className={styles.launch} onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="guide-chat">
        <Icon name="spark" size={22}/>{translate({id: 'chat.launch', message: 'Ask the guide'})}
      </button>
      {open && <section id="guide-chat" className={styles.panel}
        aria-label={translate({id: 'chat.title', message: 'Guide assistant'})}
        onKeyDown={(e) => { if (e.key === 'Escape') close(); }}>
        <header><div><span className={styles.eyebrow}>SKILLS GUIDE</span><h2>{translate({id: 'chat.title', message: 'Guide assistant'})}</h2></div>
          <button onClick={close} aria-label={translate({id: 'chat.close', message: 'Close assistant'})}>×</button></header>
        <div className={styles.context}>
          <label htmlFor="chat-plugin">{translate({id: 'chat.scope', message: 'Ask about'})}</label>
          <select id="chat-plugin" value={plugin} onChange={(e) => changePlugin(e.target.value)}>
            <option value="">{translate({id: 'chat.all', message: 'Find the right plugin'})}</option>
            {guides.map((g) => <option key={g.id} value={g.id}>{g.id}</option>)}
          </select>
        </div>
        <div className={styles.conversation} role="log" aria-live="polite" aria-relevant="additions">
          {!messages.length && <div className={styles.welcome}>
            <Icon name="spark" size={32}/><h3>{translate({id: 'chat.welcome', message: 'What are you trying to do?'})}</h3>
            <p>{translate({id: 'chat.intro', message: 'Ask about installation, a workflow or your next step. Answers use the published guides and include links to read more.'})}</p>
            <button onClick={() => setQuestion(translate({id: 'chat.exampleQuestion', message: 'How do I create my first presentation and check the speaker notes?'}))}>
              {translate({id: 'chat.exampleLabel', message: 'Help me make my first presentation'})} ↗
            </button>
          </div>}
          {messages.map((message, i) => <article key={i} className={message.role === 'user' ? styles.user : styles.assistant}>
            <strong>{message.role === 'user' ? translate({id: 'chat.you', message: 'You'}) : translate({id: 'chat.guide', message: 'Guide'})}</strong>
            <p>{message.content}</p>
            {message.degraded && <small>{translate({id: 'chat.partial', message: 'Some plugin specialists were unavailable. This answer uses the available guide evidence.'})}</small>}
            {!!message.sources?.length && <div className={styles.sources}><span>{translate({id: 'chat.sources', message: 'Read the source guides'})}</span>
              {message.sources.map((source) => <Link key={source.url} to={source.url}>{source.title} ↗</Link>)}</div>}
          </article>)}
          {busy && <p role="status" className={styles.status}>{translate({id: 'chat.thinking', message: 'Checking the relevant guides and preparing your answer…'})}</p>}
        </div>
        <div className={styles.composer}>
          {available === false && <p role="status">{translate({id: 'chat.offline', message: 'Chat is not connected in this preview. The learning paths and reference guides are available.'})}</p>}
          {error && available && <p className={styles.error} role="alert">{errorText}</p>}
          {available && !signedIn && <div className={styles.signIn}>
            <p>{translate({id: 'chat.signInHint', message: 'Sign in to ask a question. Reading the guides is always open.'})}</p>
            <button onClick={() => auth && signIn(auth).catch(() => setError('sign_in_failed'))}>{translate({id: 'chat.signIn', message: 'Sign in / create an account'})} ↗</button>
          </div>}
          <form onSubmit={send}>
            <label htmlFor="guide-question">{translate({id: 'chat.question', message: 'Your question'})}</label>
            <textarea ref={input} id="guide-question" value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={2000} rows={3}
              placeholder={translate({id: 'chat.placeholder', message: 'Tell me what you want to do…'})} disabled={busy} />
            <div><small>{translate({id: 'chat.privacy', message: 'Do not include credentials or private project data.'})}</small>
              <button type="submit" disabled={!available || !signedIn || busy || !question.trim()}>{translate({id: 'chat.send', message: 'Send'})} ↑</button></div>
          </form>
          {signedIn && <button className={styles.signOut} onClick={() => {setMessages([]); signOut(auth);}}>{translate({id: 'chat.signOut', message: 'Sign out and clear chat'})}</button>}
        </div>
      </section>}
    </>
  );
}
