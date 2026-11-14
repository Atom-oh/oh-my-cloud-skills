import React, {useEffect, useState} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {translate} from '@docusaurus/Translate';
import {useLocation} from '@docusaurus/router';
import {guides} from './guides';
import styles from './styles.module.css';

export default function GuideWorkspace() {
  const location = useLocation();
  const [selected, setSelected] = useState('aws-content-plugin');
  const [host, setHost] = useState<'claude' | 'codex'>('claude');
  const [step, setStep] = useState(0);
  const [copyState, setCopyState] = useState('');
  useEffect(() => {
    const read = () => {
      const id = new URLSearchParams(window.location.search).get('plugin');
      if (guides.some((g) => g.id === id)) setSelected(id!);
    };
    read(); window.addEventListener('popstate', read);
    return () => window.removeEventListener('popstate', read);
  }, [location.search]);
  const guide = guides.find((g) => g.id === selected)!;
  const image = useBaseUrl(guide.image || '/img/logo.svg');
  const steps = [
    translate({id: 'learn.step.install', message: 'Install'}),
    translate({id: 'learn.step.try', message: 'Try a first task'}),
    translate({id: 'learn.step.verify', message: 'Check the result'}),
  ];
  const install = host === 'claude'
    ? `/plugin marketplace add Atom-oh/oh-my-cloud-skills\n/plugin install ${guide.id}@oh-my-cloud-skills`
    : 'codex plugin marketplace add Atom-oh/oh-my-cloud-skills';
  const text = step === 0 ? install : host === 'codex' && guide.codexPrompt ? guide.codexPrompt : guide.prompt;
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopyState(translate({id: 'learn.copied', message: 'Copied'}));
    } catch {
      setCopyState(translate({id: 'learn.copyFailed', message: 'Select the text to copy it manually.'}));
    }
  }
  function choose(id: string) {
    setSelected(id); setStep(0); setCopyState('');
    const url = new URL(window.location.href);
    url.searchParams.set('plugin', id);
    window.history.replaceState(null, '', url);
    window.dispatchEvent(new CustomEvent('guide-context', {detail: id}));
  }
  function ask() {
    window.dispatchEvent(new CustomEvent('guide-chat', {detail: {plugin: guide.id, question: ''}}));
  }
  return (
    <main className={styles.workspace}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>OH MY CLOUD SKILLS <span>/</span> FIELD GUIDE</p>
          <h1>{translate({id: 'learn.heading', message: 'Less reading. More making.'})}</h1>
          <p className={styles.lead}>{translate({id: 'learn.lead', message: 'Choose what you want to do. Follow a short path, try it in your own workspace, and get help when you need it.'})}</p>
        </div>
        <div className={styles.heroNote}>
          <span className={styles.noteNumber}>06</span>
          <span>{translate({id: 'learn.sixPaths', message: 'plugins, one place to begin'})}</span>
          <Link to="/docs/intro">{translate({id: 'learn.reference', message: 'Browse the reference library'})} ↗</Link>
        </div>
      </header>
      <div className={styles.body}>
        <aside className={styles.sidebar}>
          <p className={styles.label}>{translate({id: 'learn.choose', message: 'WHAT WILL YOU MAKE NEXT?'})}</p>
          <nav aria-label={translate({id: 'learn.pluginNav', message: 'Plugin learning paths'})}>
            {guides.map((g) => (
              <button key={g.id} onClick={() => choose(g.id)} aria-current={selected === g.id ? 'page' : undefined}
                className={selected === g.id ? styles.selected : ''}>
                <span className={styles.mark}>{g.mark}</span><span><strong>{g.name}</strong><small>{g.purpose}</small></span>
              </button>
            ))}
          </nav>
          <div className={styles.sidebarNote}>
            <span className={styles.smallStar}>✳</span>
            <p>{translate({id: 'learn.sideNote', message: 'Your workspace does the work. This guide helps you take the next step.'})}</p>
            <button onClick={ask}>{translate({id: 'learn.ask', message: 'Ask the guide'})} ↗</button>
          </div>
        </aside>
        <section className={styles.lesson} aria-label={guide.title}>
          <div className={styles.lessonHeader}>
            <span className={styles.pill}>{guide.id}</span>
            <span className={styles.pathCount}>{guide.mark} / 06</span>
          </div>
          <h2>{guide.title}</h2>
          <p className={styles.description}>{guide.description}</p>
          <div className={styles.hostRow}>
            <span>{translate({id: 'learn.yourHost', message: 'Your coding assistant'})}</span>
            <div className={styles.segment}>
              <button aria-pressed={host === 'claude'} onClick={() => {setHost('claude'); setCopyState('');}}>Claude Code</button>
              <button aria-pressed={host === 'codex'} onClick={() => {setHost('codex'); setCopyState('');}}>Codex</button>
            </div>
          </div>
          {host === 'codex' && ['agent-dash', 'pr-dash'].includes(selected) && (
            <p className={styles.hostNotice}>{translate({id: 'learn.hostNotice', message: 'The live dashboard pane belongs to Claude Code. In Codex, use the installed guide or status procedure.'})}</p>
          )}
          <ol className={styles.steps}>
            {steps.map((label, i) => <li key={label}><button onClick={() => {setStep(i); setCopyState('');}}
              aria-current={step === i ? 'step' : undefined}>
              <span>{i + 1}</span>{label}
            </button></li>)}
          </ol>
          <div className={styles.stepContent} key={`${selected}-${step}`}>
            <div className={styles.action}>
              <p className={styles.label}>{translate({id: 'learn.yourTurn', message: 'YOUR TURN'})}</p>
              <h3>{steps[step]}</h3>
              <p>{step === 0
                ? (host === 'claude'
                  ? translate({id: 'learn.claudeInstall', message: 'Run these commands inside Claude Code. Reload the installed plugin if prompted, then begin a new task.'})
                  : translate({id: 'learn.codexInstall', message: 'Register the marketplace in your terminal. Then open /plugins in Codex, install the selected plugin, and start a new thread.'}))
                : step === 1
                  ? translate({id: 'learn.tryHint', message: 'Copy this starting prompt into your coding assistant. Adjust the audience, language and scope to your project.'})
                  : host === 'codex' && guide.codexCheck ? guide.codexCheck : guide.check}</p>
              {step < 2 && <div className={styles.command}>
                <div><span>{step === 0 ? (host === 'claude' ? 'Claude Code' : 'Terminal') : translate({id: 'learn.promptLabel', message: 'Starting prompt'})}</span>
                  <button onClick={copy}>{translate({id: 'learn.copy', message: 'Copy'})}</button></div>
                <pre><code>{text}</code></pre>
                <span role="status" className={styles.copyStatus}>{copyState}</span>
              </div>}
              {step === 2 && <Link className={styles.deepLink} to={guide.next}>{translate({id: 'learn.fullGuide', message: 'Open the detailed guide'})} ↗</Link>}
            </div>
            <aside className={styles.result}>
              <p className={styles.label}>{translate({id: 'learn.expected', message: 'WHAT TO EXPECT'})}</p>
              <p>{step === 0
                ? translate({id: 'learn.installResult', message: 'The plugin appears in your installed list. Installation confirms the package is present; the first task verifies the tools it needs.'})
                : host === 'codex' && guide.codexResult ? guide.codexResult : guide.result}</p>
              {guide.image && step > 0
                ? <a href={image} target="_blank" rel="noreferrer"><img src={image} alt={guide.imageAlt} loading="lazy" />
                  <span>{translate({id: 'learn.enlarge', message: 'Published example · open full size'})} ↗</span></a>
                : <div className={styles.flow}>
                  <span className={styles.flowLabel}>{translate({id: 'learn.workflow', message: 'Workflow preview'})}</span>
                  {(host === 'codex' && guide.codexExample ? guide.codexExample : guide.example).map((item, i) => <div key={item}><span>{String(i + 1).padStart(2, '0')}</span><code>{item}</code></div>)}
                </div>}
            </aside>
          </div>
          <footer className={styles.lessonFooter}>
            <Link to={guide.setup}>{translate({id: 'learn.setupHelp', message: 'Setup & troubleshooting'})} ↗</Link>
            {step < 2 ? <button className={styles.next} onClick={() => {setStep(step + 1); setCopyState('');}}>
              {steps[step + 1]} <span>→</span>
            </button> : <button className={styles.next} onClick={ask}>{translate({id: 'learn.askFollowup', message: 'Ask a follow-up'})} <span>↗</span></button>}
          </footer>
        </section>
      </div>
      <section className={styles.explore}>
        <div><p className={styles.label}>{translate({id: 'learn.goDeeper', message: 'KEEP EXPLORING'})}</p>
          <h2>{translate({id: 'learn.exploreTitle', message: 'A guide for the moment you are in.'})}</h2></div>
        <Link to="/docs/remarp-guide/introduction"><span>01</span><strong>{translate({id: 'learn.author', message: 'Write a presentation'})}</strong><small>Remarp</small>↗</Link>
        <Link to="/docs/aws-content-plugin/presenter-guide"><span>02</span><strong>{translate({id: 'learn.present', message: 'Rehearse and present'})}</strong><small>{translate({id: 'learn.presenter', message: 'Presenter guide'})}</small>↗</Link>
        <Link to="/docs/intro"><span>03</span><strong>{translate({id: 'learn.allFeatures', message: 'Find a specific feature'})}</strong><small>{translate({id: 'learn.library', message: 'Reference library'})}</small>↗</Link>
      </section>
    </main>
  );
}
